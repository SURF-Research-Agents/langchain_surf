"""HPC Function"""
import json
import os
import dill

from langchain_surf.tools.utils.slurm_connector import SLURMAPIConnector
from langchain_surf.tools.utils.object_store_connector_cli import (
    ObjectStoreConnectorCLI as OSConnector,
)


class HPCFunc:
    """Wrap a Python function for execution on an HPC cluster via SLURM.

    This class serializes a callable using ``dill``, uploads it to an
    S3-compatible object store, submits a SLURM job that downloads the
    serialized function, executes it, and retrieves the JSON output.

    The typical workflow is:

    1. Serialize the wrapped function with ``dill``.
    2. Create a bucket and upload the serialized function plus a small
       Python wrapper script to the object store.
    3. Submit a SLURM job that syncs the files from the object store,
       runs the wrapper, and syncs the results back.
    4. Read the JSON output file from the object store once the job
       completes.

    Parameters
    ----------
    func : callable
        The function to execute on the HPC cluster.
    slurm_data : dict
        Configuration dictionary for the SLURM API connector. Must contain
        at minimum the keys required by ``SLURMAPIConnector`` (e.g. ``url``,
        ``api_ver``, ``user_name``, ``slurm_jwt``).
    os_data : dict, optional
        Configuration dictionary for the Object Store connector. Must contain
        at minimum the keys required by ``ObjectStoreConnectorCLI`` (e.g.
        ``url``, ``os_access_key``, ``os_secret_key``). Defaults to ``None``.
    dill_file_name : str, optional
        Filename for the serialized function. Defaults to
        ``'serialized_func.pkl'``.
    json_output_file_name : str, optional
        Filename for the JSON output written by the executed function.
        Defaults to ``'json_output.json'``.
    python_file_name : str, optional
        Filename for the Python wrapper script. Defaults to
        ``'execute_python_script.py'``.
    container_image : str, optional
        Path or URI of the container image (Singularity/Apptainer) to run
        the job inside. If ``None``, the job runs directly on the cluster
        without a container. Defaults to ``None``.

    Examples
    --------
    >>> def my_func(x, y):
    ...     return x + y
    >>> hpc_func = HPCFunc(
    ...     func=my_func,
    ...     slurm_data={"url": "...", "api_ver": "...", ...},
    ...     os_data={"url": "...", "os_access_key": "...", ...},
    ... )
    >>> result = hpc_func(1, 2)
    """

    def __init__(
        self,
        func,
        slurm_data,
        os_data=None,
        dill_file_name="serialized_func.pkl",
        json_output_file_name="json_output.json",
        python_file_name="execute_python_script.py",
        container_image=None,
    ):

        self.func = func
        self.dill_file_name = dill_file_name
        self.json_output_file_name = json_output_file_name
        self.python_file_name = python_file_name
        self.container_image = container_image

        self.slurm_connector = SLURMAPIConnector(slurm_data)
        self.os_connector = OSConnector(os_data)

        self.slurm_data = self.slurm_connector.settings
        self.os_data = self.os_connector.settings

        if self.container_image is not None:
            self.container_image = f"../containers/{self.container_image}"

    def _write_python_script(self):
        """Write a Python wrapper script that loads and executes the serialized function.

        The generated script imports ``dill`` and ``json``, loads the pickled
        function from ``self.dill_file_name``, calls it, and writes the result
        to ``self.json_output_file_name``.

        Returns
        -------
        str
            The content of the generated Python script as a string.
        """
        file_str = []
        file_str += ["import dill"]
        file_str += ["import json"]
        file_str += [f"with open('{self.dill_file_name}', 'rb') as fopen:"]
        file_str += ["    exec_tool = dill.load(fopen)"]
        file_str += ["status = exec_tool()"]

        with open(self.python_file_name, "w", encoding="utf-8") as file:
            file.write("\n".join(file_str))

        return "\n".join(file_str)

    def _bash_script(self):
        """Generate a bash script for downloading, executing, and uploading results.

        The generated script:
        1. Activates the virtual environment (or uses the container).
        2. Creates and enters a directory named after the object store bucket.
        3. Syncs files from the object store to the local directory.
        4. Executes the Python wrapper script (inside a container if configured).
        5. Syncs the results back to the object store.

        Returns
        -------
        str
            The content of the generated bash script as a string.
        """
        file_str = []
        file_str += ["#!/bin/bash"]

        if self.container_image:
            # Run inside a Singularity/Apptainer container
            file_str += [
                f'mkdir {self.os_data["bucketname"]}',
                f'cd {self.os_data["bucketname"]}',
                f"aws s3 sync s3://{self.os_data['bucketname']}/ .",
                f'apptainer run --bind $(pwd) {self.container_image} {self.python_file_name}',
                f"aws s3 sync . s3://{self.os_data['bucketname']}/",
            ]
        else:
            # Run directly on the cluster
            file_str += [
                "source .venv/bin/activate",
                f'mkdir {self.os_data["bucketname"]}',
                f'cd {self.os_data["bucketname"]}',
                f"aws s3 sync s3://{self.os_data['bucketname']}/ .",
                f"python {self.python_file_name}",
                f"aws s3 sync . s3://{self.os_data['bucketname']}/",
            ]
        return "\n".join(file_str)

    def __call__(self, *args, **kwargs):
        """Execute the wrapped function on an HPC cluster via SLURM.

        This method serializes the wrapped function using ``dill``, uploads
        it to the object store, submits a SLURM job, waits for completion,
        and retrieves the JSON output.

        The workflow is:
        1. Serialize the function with its arguments using ``dill``.
        2. Write a Python wrapper script.
        3. Create a bucket and upload the serialized function and wrapper.
        4. Submit and monitor a SLURM job.
        5. Read the JSON output from the object store.
        6. Clean up temporary files.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to the wrapped function.
        **kwargs : dict
            Keyword arguments to pass to the wrapped function.

        Returns
        -------
        result
            The JSON-parsed result from the executed function.

        Examples
        --------
        >>> def add(a, b):
        ...     return a + b
        >>> hpc_func = HPCFunc(add, slurm_data=slurm_data, os_data=os_data)
        >>> hpc_func(1, 2)
        3
        """

        try:
            # defined the function to be serialized
            def serialized_call():
                """Serializes and executes the wrapped function, writing JSON output.

                This function is pickled with dill, uploaded to the object store,
                and executed on a remote HPC node via SLURM.
                """
                try:
                    with open(
                        self.json_output_file_name, "w", encoding="utf-8"
                    ) as file:
                        json.dump(self.func(*args, **kwargs), file, indent=4)
                    return True
                except Exception as e:
                    print(e)
                    return False

            # serialize the function
            with open(self.dill_file_name, "wb") as fopen:
                dill.dump(serialized_call, fopen, recurse=False)

            # write the python script
            self._write_python_script()

            # upload all the files to the object store
            self.os_connector.create_bucket()
            self.os_connector.upload_files_to_os(
                [self.python_file_name, self.dill_file_name]
            )

            # submit the job to the SLURM API
            self.slurm_connector.submit_and_monitor_slurm_job(
                job_script=self._bash_script(), monitor_interval=10
            )

            result = self.os_connector.read_files_from_os(self.json_output_file_name)

            return result

        finally:
            # Clean up temporary files
            for f in (self.python_file_name, self.dill_file_name):
                if os.path.exists(f):
                    os.unlink(f)

def hpc_func(slurm_data):
    """Decorator that wraps a function for execution on an HPC cluster via SLURM.

    Parameters
    ----------
    slurm_data : dict
        Configuration dictionary passed to ``HPCFunc``.

    Returns
    -------
    callable
        A decorator that converts the wrapped function into an ``HPCFunc``.

    Examples
    --------
    >>> @run_on_hpc(slurm_data)
    ... def add(a, b):
    ...     return a + b
    >>> result = add(1, 2)  # executes remotely on SLURM
    """
    def hpc_decorator(func):
        return HPCFunc(func, slurm_data=slurm_data)
    return hpc_decorator

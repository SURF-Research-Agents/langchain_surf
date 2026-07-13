import time
import requests


class SLURMAPIConnector:
    """Connector for interacting with the SLURM REST API.

    Provides methods to submit jobs, monitor their status, and combine
    both operations into a single call. Authentication is handled via
    SLURM username and JWT token passed through the ``settings`` dict.

    Parameters
    ----------
    settings : dict
        Configuration dictionary containing at minimum the required keys
        (see ``required_settings`` below). Additional keys configure job
        defaults (partition, time limit, CPU/GPU counts, etc.).
    default_settings : dict, optional
        Fallback values for optional job parameters. Defaults to a
        minimal configuration with a 120-second time limit on the
        ``rome`` partition.

    required_settings
        The following keys must be present in ``settings``:

        - ``user_name`` – SLURM username
        - ``slurm_jwt`` – JWT authentication token
        - ``url`` – Base URL of the SLURM REST API
        - ``api_ver`` – API version string (e.g. ``v23``)

    Examples
    --------
    >>> settings = {
    ...     "user_name": "myuser",
    ...     "slurm_jwt": "abc123token",
    ...     "url": "https://slurm-cluster.example.com",
    ...     "api_ver": "v23",
    ... }
    >>> connector = SLURMAPIConnector(settings)
    >>> connector.settings["time"] = 300  # 5 minutes
    >>> connector.settings["jobname"] = "my_experiment"
    >>> status, job_id = connector.submit_job("#!/bin/bash\\necho hello")
    """

    def __init__(self, settings, default_settings=None):
        self.settings = settings

        required_settings = ["user_name", "slurm_jwt", "url", "api_ver"]

        if default_settings is None:
            default_settings = {
                "jobname": "slurm_api",
                "time": 120,
                "partition": "rome",
                "nodes": 1,
                "tasks": 1,
                "cpus_per_task": 1,
            }

        self._update_settings(default_settings)
        self._validate_settings(required_settings)

    def _update_settings(self, new_settings):
        """
        Updates the settings dictionary with the provided new settings.

        The following settings are also added if not already present:
        - output_file_name: The name of the output file. Defaults to jobname.out
        - error_file_name: The name of the error file. Defaults to jobname.err
        - cwd: The current working directory for the job. Defaults to /home/user_name/test_rsa/

        Parameters
        ----------
        new_settings : dict
            A dictionary containing the new settings to be added.

        Returns
        -------
        None
        """
        self.settings.update(new_settings)
        if "output_file_name" not in self.settings:
            self.settings["output_file_name"] = self.settings["jobname"] + ".out"
        if "error_file_name" not in self.settings:
            self.settings["error_file_name"] = self.settings["jobname"] + ".err"
        if "cwd" not in self.settings:
            self.settings["cwd"] = "/home/" + self.settings["user_name"] + "/test_rsa/"

    def _validate_settings(self, required_settings):
        for setting in required_settings:
            if setting not in self.settings:
                raise ValueError(f"Missing required setting: {setting}")

    def submit_job(self, job_script_str):
        """Submits a job to the SLURM API.

        Parameters
        ----------
        slurm_data : dict
            A dictionary containing the SLURM API credentials.
        job_script_str : str
            The script to be executed by the job.

        Returns:
        -------
        job_in_progress : bool
            A boolean indicating if the job is still in progress.
        job_id : str
            The ID of the submitted job.

        Notes:
        -----
        This function is used to submit a job to the SLURM API.
        """
        headers = {
            "X-SLURM-USER-NAME": f"{self.settings['user_name']}",
            "X-SLURM-USER-TOKEN": f"{self.settings['slurm_jwt']}",
        }

        # print(headers)

        payload = {
            "job": {
                "partition": self.settings["partition"],
                "standard_output": self.settings["output_file_name"],
                "standard_error": self.settings["error_file_name"],
                "name": self.settings["jobname"],
                "time_limit": {"set": True, "number": self.settings["time"]},
                "current_working_directory": self.settings["cwd"],
                "nodes": self.settings["nodes"],
                "tasks": self.settings["tasks"],
                "cpus_per_task": self.settings["cpus_per_task"],
                "environment": {
                    "USER": self.settings["user_name"],
                },
            },
            "script": job_script_str,
        }

        # print(payload)
        response = requests.post(
            f"{self.settings['url']}/slurm/{self.settings['api_ver']}/job/submit",
            headers=headers,
            json=payload,
            timeout=30,
        )

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            job_in_progress = True
            job_id = response_data["job_id"]  # check the actual key for job id in the response
        else:
            job_in_progress = False
            raise Warning(f"Failed to submit job: {response.status_code} - {response.text}")
        return job_in_progress, job_id

    def monitor_slurm_job_status(self, job_in_progress: bool, job_id: str, monitor_interval=60):
        """Monitors the status of a SLURM job with the given job_id until it is completed.

        Parameters
        ----------
        slurm_data : dict
            A dictionary containing the SLURM API credentials.
        job_in_progress : bool
            A boolean indicating if the job is still in progress.
        job_id : str
            The ID of the job to be monitored.
        monitor_interval : int, optional
            The interval in seconds at which the job status should be checked.

        Returns:
        -------
        job_in_progress : bool
            A boolean indicating if the job is still in progress.

        Notes:
        -----
        This function is used to monitor the status of a SLURM job with the given job_id until it is completed.
        """
        while job_in_progress:
            response = requests.get(
                f"{self.settings['url']}/slurm/{self.settings['api_ver']}/job/{job_id}",
                headers={
                    "X-SLURM-USER-NAME": f"{self.settings['user_name']}",
                    "X-SLURM-USER-TOKEN": f"{self.settings['slurm_jwt']}",
                },
                timeout=30,
            )

            response = response.json()
            job_status = response["jobs"][0]["job_state"][0]
            if job_status == "COMPLETED":
                job_in_progress = False
                print(f"Job {job_id} completed successfully.")
                break
            if job_status in ["FAILED", "CANCELLED", "TIMEOUT"]:
                job_in_progress = False
                print(f"Job {job_id} failed with state: {job_status}")
            else:
                print(f"Job {job_id} is still in progress with state: {job_status}")

            time.sleep(monitor_interval)

        return job_in_progress

    def submit_and_monitor_slurm_job(self, job_script, monitor_interval=60):
        """Submits a job to the SLURM API and monitors its status until it is completed.

        Parameters
        ----------
        job_script : str
            The script to be executed by the job.

        Returns:
        -------
        job_status : bool
            A boolean indicating if the job is still in progress.

        Notes:
        -----
        This function is used to submit a job to the SLURM 
        API and monitor its status until it is completed.
        """
        job_status, job_id = self.submit_job(job_script)
        job_status = self.monitor_slurm_job_status(job_status,
                                                   job_id,
                                                   monitor_interval=monitor_interval)
        return job_status

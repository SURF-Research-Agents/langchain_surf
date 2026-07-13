import json
import os
import tempfile
import uuid
import shutil
import subprocess


class ObjectStoreConnectorCLI:
    """Connector for interacting with an S3-compatible Object Store via the AWS CLI.

    Provides the same bucket and object operations as ``ObjectStoreConnector``,
    but all work is delegated to ``aws`` CLI commands rather than the ``boto3``
    library. This avoids to have to pass the OS credentials.

    Parameters
    ----------
    os_data : dict
        Configuration dictionary containing at minimum the required keys
        (see ``required_settings`` below).
    job_name : str, optional
        Prefix used when generating a unique bucket name. Defaults to
        ``"generic"``.

    required_settings
        The following keys must be present in ``os_data``:

        - ``url`` – S3-compatible endpoint URL
        - ``os_access_key`` – Access key ID
        - ``os_secret_key`` – Secret access key
        - ``bucketname`` – Bucket name (auto-generated with UUID prefix if omitted)

    Examples
    --------
    >>> connector = ObjectStoreConnectorCLI(os_data={'bucketname':'test_cli'})
    >>> connector.create_bucket()
    >>> connector.upload_files_to_os("results.csv", "results.csv")
    """

    def __init__(self, os_data=None, job_name="generic"):
        self.settings = os_data if os_data is not None else {}
        self.job_name = job_name
        required_settings = ["bucketname"]

        self._update_bucket_name()
        self._validate_settings(required_settings)

    def _get_uuid_bucketname(self):
        """Returns a unique name for the Object Store bucket.

        Returns
        -------
        str
            A unique name for the Object Store bucket.
        """
        iid = str(uuid.uuid4())
        return "sra_" + self.job_name + "_" + iid

    def _update_bucket_name(self):
        """Updates ``self.settings`` with a default bucket name if not provided."""
        if "bucketname" not in self.settings:
            self.settings["bucketname"] = self._get_uuid_bucketname()

    def _validate_settings(self, required_settings):
        for setting in required_settings:
            if setting not in self.settings:
                raise ValueError("Setting not defined")

    def create_bucket(self):
        """Creates a bucket in the Object Store using the AWS CLI.

        Executes ``aws s3api create-bucket`` with the connector's
        endpoint URL, access key, and secret key.

        Raises
        ------
        RuntimeError
            If the AWS CLI command returns a non-zero exit code.
        """
        bucket = self.settings["bucketname"]
        print(f"Creates bucket {bucket} in Object Store")

        cmd = [
            "aws",
            "s3api",
            "create-bucket",
            "--bucket",
            bucket,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create bucket via CLI: {result.stderr.strip()}"
            )
        return result.stdout

    def delete_bucket(self):
        """Deletes a bucket in the Object Store using the AWS CLI.

        Executes ``aws s3api delete-bucket`` with the connector's
        endpoint URL, access key, and secret key.

        Raises
        ------
        RuntimeError
            If the AWS CLI command returns a non-zero exit code.
        """
        bucket = self.settings["bucketname"]
        print(f"Deletes bucket {bucket} in Object Store ")

        cmd = [
            "aws",
            "s3api",
            "delete-bucket",
            "--bucket",
            bucket,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to delete bucket via CLI: {result.stderr.strip()}"
            )
        return result.stdout

    def purge_bucket(self):
        """Purges a bucket in the Object Store using the AWS CLI.

        Deletes all objects in the bucket first, then deletes the bucket
        itself via ``aws s3api`` commands.

        Raises
        ------
        RuntimeError
            If any AWS CLI command returns a non-zero exit code.
        """
        bucket = self.settings["bucketname"]
        print(f"Purges bucket {bucket} in Object Store ")

        # Delete all objects in the bucket
        list_cmd = [
            "aws",
            "s3api",
            "list-objects-v2",
            "--bucket",
            bucket,
        ]
        list_result = subprocess.run(
            list_cmd, capture_output=True, text=True, check=False
        )
        if list_result.returncode != 0:
            raise RuntimeError(
                f"Failed to list objects via CLI: {list_result.stderr.strip()}"
            )

        stdout = json.loads(list_result.stdout) if list_result.stdout.strip() else {}
        objects = stdout.get("Contents", [])
        if objects:
            delete_payload = json.dumps(
                {"Objects": [{"Key": obj["Key"]} for obj in objects]}
            )
            delete_cmd = [
                "aws",
                "s3api",
                "delete-objects",
                "--bucket",
                bucket,
                "--delete",
                delete_payload,
            ]
            del_result = subprocess.run(
                delete_cmd, capture_output=True, text=True, check=False
            )
            if del_result.returncode != 0:
                raise RuntimeError(
                    f"Failed to delete objects via CLI: {del_result.stderr.strip()}"
                )

        # Delete the bucket
        delete_bucket_cmd = [
            "aws",
            "s3api",
            "delete-bucket",
            "--bucket",
            bucket,
        ]
        result = subprocess.run(
            delete_bucket_cmd, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to delete bucket via CLI: {result.stderr.strip()}"
            )
        return result.stdout

    def upload_files_to_os(self, filename, objectname=None):
        """Uploads files to the Object Store using the AWS CLI.

        Executes ``aws s3 cp`` for each file, uploading to the
        configured bucket with the specified object key.

        Parameters
        ----------
        filename : str or list of str
            Local file path(s) to upload.
        objectname : str or list of str, optional
            Object key(s) in the bucket. Defaults to the filename(s).

        Raises
        ------
        RuntimeError
            If any AWS CLI command returns a non-zero exit code.
        """
        if not isinstance(filename, list):
            filename = [filename]
        if objectname is None:
            objectname = filename
        if not isinstance(objectname, list):
            objectname = [objectname]

        bucket = self.settings["bucketname"]

        for fn, obj in zip(filename, objectname, strict=True):
            print(f"Upload file {fn} to bucket as object {obj} ")
            cmd = [
                "aws",
                "s3",
                "cp",
                fn,
                f"s3://{bucket}/{obj}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to upload {fn} via CLI: {result.stderr.strip()}"
                )

    def put_object_to_os(self, object_data, objectname):
        """Puts an object into the Object Store using the AWS CLI.

        Writes the object data to a temporary file and executes
        ``aws s3api put-object``.

        Parameters
        ----------
        object_data : bytes or str
            The data to store in the object.
        objectname : str
            The name (key) of the object in the Object Store.

        Raises
        ------
        RuntimeError
            If the AWS CLI command returns a non-zero exit code.
        """
        bucket = self.settings["bucketname"]
        print(f"Puts object {objectname} into bucket {bucket} ")

        if isinstance(object_data, str):
            object_data = object_data.encode()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(object_data)
            tmp_path = tmp.name

        try:
            cmd = [
                "aws",
                "s3api",
                "put-object",
                "--bucket",
                bucket,
                "--key",
                objectname,
                "--body",
                tmp_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to put object via CLI: {result.stderr.strip()}"
                )
            return result.stdout
        finally:
            os.unlink(tmp_path)

    def read_files_from_os(self, objectname):
        """Reads file(s) from the Object Store using the AWS CLI.

        Downloads the object(s) via ``aws s3 cp`` to a temporary
        directory, reads their contents, and cleans up the temp files.

        Parameters
        ----------
        objectname : str or list of str
            Object key(s) in the bucket to read.

        Returns
        -------
        list of str
            The decoded content of each requested object.

        Raises
        ------
        RuntimeError
            If any AWS CLI command returns a non-zero exit code.
        """
        if not isinstance(objectname, list):
            objectname = [objectname]

        bucket = self.settings["bucketname"]
        tmp_dir = tempfile.mkdtemp()
        contents = []

        try:
            for obj in objectname:
                local_path = os.path.join(tmp_dir, os.path.basename(obj))
                print(f"Reads object {obj} from bucket {bucket} via AWS CLI")

                cmd = [
                    "aws",
                    "s3api",
                    "get-object",
                    "--bucket",
                    bucket,
                    "--key",
                    obj,
                    local_path,
                ]
                cmd_result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )
                if cmd_result.returncode != 0:
                    raise RuntimeError(
                        f"Failed to get {obj} via CLI: {cmd_result.stderr.strip()}"
                    )

                with open(local_path, "r", encoding="utf-8") as f:
                    contents.append(f.read())

            return contents
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Demonstrate ObjectStoreConnectorCLI usage."
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default="demo_cli_bucket",
        help="Bucket name (default: demo_cli_bucket)",
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["create", "upload", "put", "purge", "delete", "read", "all"],
        default="create",
        help="Action to perform (default: all)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="File to upload/read (required for --action upload/read)",
    )

    args = parser.parse_args()

    settings = {"bucketname": args.bucket}
    connector = ObjectStoreConnectorCLI(os_data=settings, job_name="demo")

    if args.action in ("create", "all"):
        connector.create_bucket()

    if args.action in ("upload", "all"):
        target_file = args.file or __file__
        connector.upload_files_to_os(target_file, os.path.basename(target_file))

    if args.action in ("put", "all"):
        connector.put_object_to_os("Hello from CLI!", "hello.txt")

    if args.action in ("purge", "all"):
        connector.purge_bucket()

    if args.action in ("delete", "all"):
        connector.delete_bucket()

    if args.action in ("read", "all"):
        if args.file:
            file_data = connector.read_files_from_os(args.file)
            print(file_data)
        else:
            raise ValueError("Specify a file to read")

    print("Done.")

import uuid
import boto3


class ObjectStoreConnector:
    """Connector for interacting with an S3-compatible Object Store.

    Provides methods to create, delete, and purge buckets, as well as
    upload, download, and put raw objects. Authentication is handled via
    access key / secret key passed through the ``settings`` dict.

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
    >>> settings = {
    ...     "url": "https://s3.example.com",
    ...     "os_access_key": "AKIAIOSFODNN7EXAMPLE",
    ...     "os_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    ... }
    >>> connector = ObjectStoreConnector(settings, job_name="experiment1")
    >>> connector.create_bucket()
    >>> connector.upload_files_to_os("results.csv", "results.csv")
    >>> data = connector.read_files_from_os("results.csv")
    """

    def __init__(self, os_data, job_name="generic"):
        self.settings = os_data
        self.job_name = job_name
        required_settings = ["url", "os_access_key", "os_secret_key", "bucketname"]

        self._update_bucket_name()
        self._validate_settings(required_settings)

    def _get_uuid_bucketname(self):
        """Returns a unique name for the Object Store bucket.

        Returns:
        -------
        str
            A unique name for the Object Store bucket.
        """
        iid = str(uuid.uuid4())
        return "sra_" + self.job_name + "_" + iid

    def _update_bucket_name(self):
        """Updates the self.os_data dictionary with default Object Store settings
        if the corresponding key does not already exist.

        This function is used to ensure that all required Object Store settings are present
        in the self.os_data dictionary, even if they are not explicitly provided
        by the user.
        """
        if "bucketname" not in self.settings:
            self.settings["bucketname"] = self._get_uuid_bucketname()

    def _validate_settings(self, required_settings):
        for setting in required_settings:
            if setting not in self.settings:
                raise ValueError("Setting not defined")

    def create_bucket(self):
        """Creates a bucket in the Object Store.

        Parameters
        ----------
        self : ObjectStoreConnector
            The instance of the ObjectStoreConnector.
        os_data : dict
            A dictionary containing the information to create a bucket in the Object Store.

        Notes:
        -----
        This function is used to create a bucket in the Object Store.
        """
        resource = boto3.client(
            "s3",
            "default",
            endpoint_url=self.settings["url"],
            aws_access_key_id=self.settings["os_access_key"],
            aws_secret_access_key=self.settings["os_secret_key"],
        )

        print("Creates bucket " + self.settings["bucketname"] + " in Object Store")
        _ = resource.create_bucket(Bucket=self.settings["bucketname"])

    def delete_bucket(self):
        """Deletes a bucket in the Object Store.

        Parameters
        ----------
        self : ObjectStoreConnector
            The instance of the ObjectStoreConnector.
        os_data : dict
            A dictionary containing the information to delete a bucket in the Object Store.

        Notes:
        -----
        This function is used to delete a bucket in the Object Store.
        """
        resource = boto3.client(
            "s3",
            "default",
            endpoint_url=self.settings["url"],
            aws_access_key_id=self.settings["os_access_key"],
            aws_secret_access_key=self.settings["os_secret_key"],
        )
        print("Deletes bucket " + self.settings["bucketname"] + " in Object Store")
        _ = resource.delete_bucket(Bucket=self.settings["bucketname"])

    def purge_bucket(self):
        """Purges a bucket in the Object Store.

        Parameters
        ----------
        self : ObjectStoreConnector
            The instance of the ObjectStoreConnector.

        Notes:
        -----
        This function is used to purge a bucket in the Object Store.
        """
        print("Purges bucket " + self.settings["bucketname"] + " in Object Store")
        resource = boto3.resource(
            "s3",
            "default",
            endpoint_url=self.settings["url"],
            aws_access_key_id=self.settings["os_access_key"],
            aws_secret_access_key=self.settings["os_secret_key"],
        )

        bucket = resource.Bucket(self.settings["bucketname"])
        bucket.objects.all().delete()
        bucket.delete()

    def upload_files_to_os(self, filename, objectname=None):
        """Uploads a file to the Object Store.

        Parameters
        ----------
        self : ObjectStoreConnector
            The instance of the ObjectStoreConnector.
        os_data : dict
            A dictionary containing the information to upload a file to the Object Store.

        Notes:
        -----
        This function is used to upload a file to the Object Store.
        """
        if not isinstance(filename, list):
            filename = [filename]

        if objectname is None:
            objectname = filename

        resource = boto3.client(
            "s3",
            "default",
            endpoint_url=self.settings["url"],
            aws_access_key_id=self.settings["os_access_key"],
            aws_secret_access_key=self.settings["os_secret_key"],
        )

        # upload files
        for fn, obj in zip(filename, objectname, strict=True):
            print("Upload file " + fn + " to bucket as object " + obj)
            with open(fn, "rb") as data:
                resource.upload_fileobj(data, self.settings["bucketname"], obj)

    def put_object_to_os(self, object_data, objectname):
        """Puts an object into the Object Store.

        Parameters
        ----------
        object : bytes
            The object to be put into the Object Store.
        objectname : str
            The name of the object in the Object Store.

        Notes:
        -----
        This function is used to put an object into the Object Store.
        """
        resource = boto3.client(
            "s3",
            "default",
            endpoint_url=self.settings["url"],
            aws_access_key_id=self.settings["os_access_key"],
            aws_secret_access_key=self.settings["os_secret_key"],
        )

        if isinstance(object_data, str):
            object_data = object_data.encode()
        resource.put_object(
            Body=object_data, Bucket=self.settings["bucketname"], Key=objectname
        )

    def read_files_from_os(self, objectname):
        """Reads a file from the Object Store.

        Parameters
        ----------
        self : ObjectStoreConnector
            The instance of the ObjectStoreConnector.
        os_data : dict
            A dictionary containing the information to read a file from the Object Store.

        Returns:
        -------
        str
            The content of the file read from the Object Store.

        Notes:
        -----
        This function is used to read a file from the Object Store.
        """
        if not isinstance(objectname, list):
            objectname = [objectname]

        s3_client = boto3.client(
            "s3",
            "default",
            endpoint_url=self.settings["url"],
            aws_access_key_id=self.settings["os_access_key"],
            aws_secret_access_key=self.settings["os_secret_key"],
        )
        data = []
        for obj in objectname:
            s3_object = s3_client.get_object(
                Bucket=self.settings["bucketname"], Key=obj
            )
            data.append(s3_object["Body"].read().decode("utf-8"))

        return data

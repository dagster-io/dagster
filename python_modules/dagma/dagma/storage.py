"""Storage for dagma."""


class Storage(object):
    """S3 backend for storage."""

    def __init__(self, config):
        self.s3_bucket = config['s3_bucket']
        self.sessionmaker = config['sessionmaker']
        self.put_object_kwargs = config['put_object_kwargs']

    @property
    def session(self):
        """The boto3 session."""
        return self.sessionmaker()

    @property
    def client(self):
        """The S3 client."""
        return self.session.client('s3')

    def put_object(self, key, body, **kwargs):
        """Put an object into the S3 backend.

        Args:
            key (str): The S3 key to use.
            body (bytes or file): The body of the object.

        Kwargs:
            Takes optional kwargs for boto3.S3.Client.put_object:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_object
        """
        return self.client.put_object(
            Bucket=self.s3_bucket, Key=key, Body=body, **dict(self.put_object_kwargs, **kwargs)
        )

    def get_object(self, key):
        """Get an object from the S3 backend.

        Args:
            key (str): The S3 key to retrieve.

        Kwargs:
            Takes optional kwargs for boto3.S3.Client.get_object:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_object
        """
        return self.client.get_object(Bucket=self.s3_bucket, Key=key)

    # TODO Use this to implement cancellation as well ?
    # def put_cancelled

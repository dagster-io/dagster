from google.cloud import storage

from dagster import resource


class GCSResource:
    def __init__(self, client=None):
        self.client = client or storage.client.Client()


@resource
def gcs_resource(_):
    return GCSResource()

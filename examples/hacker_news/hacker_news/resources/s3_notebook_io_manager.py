from dagster import io_manager
from dagstermill.io_managers import OutputNotebookIOManager

from .fixed_s3_pickle_io_manager import s3_client


class S3OutputNotebookIOManager(OutputNotebookIOManager):
    """Defines an IOManager that will store dagstermill output notebooks on s3"""

    def _get_key(self, context) -> str:
        return "notebooks/" + "_".join(context.get_run_scoped_output_identifier())

    def load_input(self, context) -> bytes:
        key = self._get_key(context.upstream_output)
        bucket = context.resources.s3_bucket
        context.log.info("loading from: s3_bucket[%s], s3_key[%s]", bucket, key)
        return s3_client().get_object(Bucket=bucket, Key=key)["Body"].read()

    def handle_output(self, context, obj: bytes):
        key = self._get_key(context)
        bucket = context.resources.s3_bucket
        context.log.info("storing to: s3_bucket[%s], s3_key[%s]", bucket, key)
        s3_client().put_object(Bucket=bucket, Key=key, Body=obj)


@io_manager(required_resource_keys={"s3_bucket"})
def s3_notebook_io_manager(_) -> OutputNotebookIOManager:
    return S3OutputNotebookIOManager()

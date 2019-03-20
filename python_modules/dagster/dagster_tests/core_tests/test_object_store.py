import os
import shutil
import uuid

from dagster import PipelineDefinition, RunConfig, seven
from dagster.core.execution import yield_pipeline_execution_context
from dagster.core.object_store import FileSystemObjectStore  # , S3ObjectStore
from dagster.core.types.runtime import Bool


def test_file_system_object_store():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)
    assert object_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    try:
        with yield_pipeline_execution_context(
            PipelineDefinition([]), {}, RunConfig(run_id=run_id)
        ) as context:
            object_store.set_object(True, context, Bool.inst(), ['true'])

        assert object_store.has_object(context, ['true'])
        assert object_store.get_object(context, Bool.inst(), ['true']) is True
    finally:
        try:
            shutil.rmtree(object_store.root)
        except seven.FileNotFoundError:
            pass

from dagster import Field, StringSource, SystemStorageData, system_storage
from dagster.core.storage.intermediates_manager import IntermediateStoreIntermediatesManager
from dagster.core.storage.system_storage import fs_system_storage, mem_system_storage

from .file_manager import ADLS2FileManager
from .intermediate_store import ADLS2IntermediateStore


@system_storage(
    name='adls2',
    is_persistent=True,
    config_schema={
        'adls2_file_system': Field(StringSource, description='ADLS Gen2 file system name'),
        'adls2_prefix': Field(StringSource, is_required=False, default_value='dagster'),
    },
    required_resource_keys={'adls2'},
)
def adls2_system_storage(init_context):
    '''Persistent system storage using Azure Data Lake Storage Gen2 for storage.

    Suitable for intermediates storage for distributed executors, so long as
    each execution node has network connectivity and credentials for ADLS and
    the backing container.

    Attach this system storage definition, as well as the :py:data:`~dagster_azure.adls2_resource`
    it requires, to a :py:class:`~dagster.ModeDefinition` in order to make it available to your
    pipeline:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[
                ModeDefinition(
                    resource_defs={'adls2': adls2_resource, ...},
                    system_storage_defs=default_system_storage_defs + [adls2_system_storage, ...],
                    ...
                ), ...
            ], ...
        )

    You may configure this storage as follows:

    .. code-block:: YAML

        storage:
          adls2:
            config:
              adls2_sa: my-best-storage-account
              adls2_file_system: my-cool-file-system
              adls2_prefix: good/prefix-for-files-
    '''
    resource = init_context.resources.adls2
    adls2_base = '{prefix}/storage/{run_id}/files'.format(
        prefix=init_context.system_storage_config['adls2_prefix'],
        run_id=init_context.pipeline_run.run_id,
    )
    return SystemStorageData(
        file_manager=ADLS2FileManager(
            adls2_client=resource.adls2_client,
            file_system=init_context.system_storage_config['adls2_file_system'],
            prefix=adls2_base,
        ),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            ADLS2IntermediateStore(
                file_system=init_context.system_storage_config['adls2_file_system'],
                run_id=init_context.pipeline_run.run_id,
                adls2_client=resource.adls2_client,
                blob_client=resource.blob_client,
                prefix=init_context.system_storage_config['adls2_prefix'],
                type_storage_plugin_registry=init_context.type_storage_plugin_registry,
            )
        ),
    )


adls2_plus_default_storage_defs = [mem_system_storage, fs_system_storage, adls2_system_storage]

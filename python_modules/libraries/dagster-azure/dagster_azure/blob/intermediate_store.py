from dagster import check
from dagster.core.storage.intermediate_store import IntermediateStore
from dagster.core.storage.type_storage import TypeStoragePluginRegistry

from .object_store import AzureBlobObjectStore


class AzureBlobIntermediateStore(IntermediateStore):
    '''Intermediate store using Azure Blob storage.

    If your storage account has the ADLS Gen2 hierarchical namespace enabled
    this should still work, but it is recommended to use the
    :py:class:`~dagster_azure.adls2.intermediate_store.ADLS2IntermediateStore`
    instead, which will enable some optimizations for certain types (notably
    PySpark DataFrames).
    '''

    def __init__(
        self, container, run_id, client, type_storage_plugin_registry=None, prefix='dagster',
    ):
        check.str_param(container, 'container')
        check.str_param(prefix, 'prefix')
        check.str_param(run_id, 'run_id')

        object_store = AzureBlobObjectStore(container, client)

        def root_for_run_id(r_id):
            return object_store.key_for_paths([prefix, 'storage', r_id])

        super(AzureBlobIntermediateStore, self).__init__(
            object_store,
            root_for_run_id=root_for_run_id,
            run_id=run_id,
            type_storage_plugin_registry=check.inst_param(
                type_storage_plugin_registry
                if type_storage_plugin_registry
                else TypeStoragePluginRegistry(types_to_register=[]),
                'type_storage_plugin_registry',
                TypeStoragePluginRegistry,
            ),
        )

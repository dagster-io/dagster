import logging
import re
import sys
from io import BytesIO, StringIO

from azure.core.exceptions import ResourceNotFoundError

from dagster import check
from dagster.core.definitions.events import ObjectStoreOperation, ObjectStoreOperationType
from dagster.core.storage.object_store import ObjectStore
from dagster.core.types.marshal import SerializationStrategy

DEFAULT_LEASE_DURATION = 60 * 60  # One hour


class AzureBlobObjectStore(ObjectStore):
    def __init__(self, container, client, lease_duration=DEFAULT_LEASE_DURATION):
        self.blob_client = client
        self.container_client = self.blob_client.get_container_client(container)

        self.lease_duration = lease_duration
        self.container_client.get_container_properties()
        super(AzureBlobObjectStore, self).__init__('azure-blob', sep='/')

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, 'key')

        logging.info('Writing Azure Blob object at: ' + self.uri_for_key(key))

        # cannot check obj since could be arbitrary Python object
        check.inst_param(
            serialization_strategy, 'serialization_strategy', SerializationStrategy
        )  # cannot be none here

        blob = self.container_client.create_blob(key)
        with blob.acquire_lease(self.lease_duration) as lease:
            with BytesIO() as bytes_io:
                if serialization_strategy.write_mode == 'w' and sys.version_info >= (3, 0):
                    with StringIO() as string_io:
                        string_io = StringIO()
                        serialization_strategy.serialize(obj, string_io)
                        string_io.seek(0)
                        bytes_io.write(string_io.read().encode('utf-8'))
                else:
                    serialization_strategy.serialize(obj, bytes_io)
                bytes_io.seek(0)
                blob.upload_blob(bytes_io, lease=lease, overwrite=True)

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.SET_OBJECT,
            key=self.uri_for_key(key),
            dest_key=None,
            obj=obj,
            serialization_strategy_name=serialization_strategy.name,
            object_store_name=self.name,
        )

    def get_object(self, key, serialization_strategy=None):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')
        check.inst_param(
            serialization_strategy, 'serialization_strategy', SerializationStrategy
        )  # cannot be none here

        # FIXME we need better error handling for object store
        blob = self.container_client.download_blob(key)
        obj = serialization_strategy.deserialize(
            BytesIO(blob.readall())
            if serialization_strategy.read_mode == 'rb'
            else StringIO(blob.readall().decode(serialization_strategy.encoding))
        )
        return ObjectStoreOperation(
            op=ObjectStoreOperationType.GET_OBJECT,
            key=self.uri_for_key(key),
            dest_key=None,
            obj=obj,
            serialization_strategy_name=serialization_strategy.name,
            object_store_name=self.name,
        )

    def has_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        try:
            blob = self.container_client.get_blob_client(key)
            blob.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False

    def rm_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        for blob in self.container_client.list_blobs(key):
            self.container_client.delete_blob(blob)

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.RM_OBJECT,
            key=self.uri_for_key(key),
            dest_key=None,
            obj=None,
            serialization_strategy_name=None,
            object_store_name=self.name,
        )

    def cp_object(self, src, dst):
        check.str_param(src, 'src')
        check.str_param(dst, 'dst')

        # Manually recurse and copy anything that looks like a file.
        for src_blob_properties in self.container_client.list_blobs(src):
            # This is the only way I can find to identify a 'directory'
            if src_blob_properties['content_settings'] is None:
                # Ignore this blob
                continue
            src_blob = self.container_client.get_blob_client(src_blob_properties['name'])
            dst_blob_path = re.sub(r'^{}'.format(src), dst, src_blob_properties['name'])
            dst_blob = self.container_client.get_blob_client(dst_blob_path)
            dst_blob.start_copy_from_url(src_blob.url)

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.CP_OBJECT,
            key=self.uri_for_key(src),
            dest_key=self.uri_for_key(dst),
            object_store_name=self.name,
        )

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, 'key')
        protocol = check.opt_str_param(protocol, 'protocol', default='https://')
        return '{protocol}@{account}.blob.core.windows.net/{container}/{key}'.format(
            protocol=protocol,
            account=self.blob_client.account_name,
            container=self.container_client.container_name,
            key=key,
        )

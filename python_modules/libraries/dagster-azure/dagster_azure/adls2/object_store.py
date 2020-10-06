import logging
import re
import sys
from io import BytesIO, StringIO

from dagster import check
from dagster.core.storage.object_store import ObjectStore
from dagster.core.types.marshal import SerializationStrategy

from .utils import ResourceNotFoundError

DEFAULT_LEASE_DURATION = 60  # One minute


class ADLS2ObjectStore(ObjectStore):
    def __init__(
        self, file_system, adls2_client, blob_client, lease_duration=DEFAULT_LEASE_DURATION
    ):
        self.adls2_client = adls2_client
        self.file_system_client = self.adls2_client.get_file_system_client(file_system)
        # We also need a blob client to handle copying as ADLS doesn't have a copy API yet
        self.blob_client = blob_client
        self.blob_container_client = self.blob_client.get_container_client(file_system)

        self.lease_duration = lease_duration
        self.file_system_client.get_file_system_properties()
        super(ADLS2ObjectStore, self).__init__("adls2", sep="/")

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, "key")

        logging.info("Writing ADLS2 object at: " + self.uri_for_key(key))

        # cannot check obj since could be arbitrary Python object
        check.inst_param(
            serialization_strategy, "serialization_strategy", SerializationStrategy
        )  # cannot be none here

        if self.has_object(key):
            logging.warning("Removing existing ADLS2 key: {key}".format(key=key))
            self.rm_object(key)

        file = self.file_system_client.create_file(key)
        with file.acquire_lease(self.lease_duration) as lease:
            with BytesIO() as bytes_io:
                if serialization_strategy.write_mode == "w" and sys.version_info >= (3, 0):
                    with StringIO() as string_io:
                        string_io = StringIO()
                        serialization_strategy.serialize(obj, string_io)
                        string_io.seek(0)
                        bytes_io.write(string_io.read().encode("utf-8"))
                else:
                    serialization_strategy.serialize(obj, bytes_io)
                bytes_io.seek(0)
                file.upload_data(bytes_io, lease=lease, overwrite=True)

        return self.uri_for_key(key)

    def get_object(self, key, serialization_strategy=None):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        check.inst_param(
            serialization_strategy, "serialization_strategy", SerializationStrategy
        )  # cannot be none here

        # FIXME we need better error handling for object store
        file = self.file_system_client.get_file_client(key)
        stream = file.download_file()
        obj = serialization_strategy.deserialize(
            BytesIO(stream.readall())
            if serialization_strategy.read_mode == "rb"
            else StringIO(stream.readall().decode(serialization_strategy.encoding))
        )
        return obj, self.uri_for_key(key)

    def has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        try:
            file = self.file_system_client.get_file_client(key)
            file.get_file_properties()
            return True
        except ResourceNotFoundError:
            return False

    def rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        # This operates recursively already so is nice and simple.
        self.file_system_client.delete_file(key)

        return self.uri_for_key(key)

    def cp_object(self, src, dst):
        check.str_param(src, "src")
        check.str_param(dst, "dst")

        # Manually recurse and copy anything that looks like a file.
        for src_blob_properties in self.blob_container_client.list_blobs(src):
            # This is the only way I can find to identify a 'directory'
            if src_blob_properties["content_settings"] is None:
                # Ignore this blob
                continue
            src_blob = self.blob_container_client.get_blob_client(src_blob_properties["name"])
            new_blob_path = re.sub(r"^{}".format(src), dst, src_blob_properties["name"])
            new_blob = self.blob_container_client.get_blob_client(new_blob_path)
            new_blob.start_copy_from_url(src_blob.url)

        return (
            self.uri_for_key(src),
            self.uri_for_key(dst),
        )

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, "key")
        protocol = check.opt_str_param(protocol, "protocol", default="abfss://")
        return "{protocol}{filesystem}@{account}.dfs.core.windows.net/{key}".format(
            protocol=protocol,
            filesystem=self.file_system_client.file_system_name,
            account=self.file_system_client.account_name,
            key=key,
        )

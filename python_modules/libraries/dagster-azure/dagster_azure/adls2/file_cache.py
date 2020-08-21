from dagster import Field, Selector, StringSource, check, resource
from dagster.core.storage.file_cache import FileCache

from .file_manager import ADLS2FileHandle
from .utils import ResourceNotFoundError, create_adls2_client


class ADLS2FileCache(FileCache):
    def __init__(
        self, storage_account, file_system, prefix, credential=None, overwrite=False, client=None
    ):
        super(ADLS2FileCache, self).__init__(overwrite=overwrite)

        self.storage_account = storage_account
        self.file_system = file_system
        self.prefix = prefix

        self.client = client or create_adls2_client(storage_account, credential)

    def has_file_object(self, file_key):
        check.str_param(file_key, "file_key")
        try:
            file = self.client.get_file_client(self.file_system, self.get_full_key(file_key))
            file.get_file_properties()
        except ResourceNotFoundError:
            return False
        return True

    def get_full_key(self, file_key):
        return "{base_key}/{file_key}".format(base_key=self.prefix, file_key=file_key)

    def write_file_object(self, file_key, source_file_object):
        check.str_param(file_key, "file_key")

        adls2_key = self.get_full_key(file_key)
        adls2_file = self.client.get_file_client(file_system=self.file_system, file_path=adls2_key)
        adls2_file.upload_data(source_file_object, overwrite=True)
        return self.get_file_handle(file_key)

    def get_file_handle(self, file_key):
        check.str_param(file_key, "file_key")
        return ADLS2FileHandle(
            self.client.account_name, self.file_system, self.get_full_key(file_key)
        )


@resource(
    {
        "storage_account": Field(StringSource, description="The storage account name."),
        "credential": Field(
            Selector(
                {
                    "sas": Field(StringSource, description="SAS token for the account."),
                    "key": Field(StringSource, description="Shared Access Key for the account"),
                }
            ),
            description="The credentials with which to authenticate.",
        ),
        "prefix": Field(StringSource, description="The base path prefix to use in ADLS2"),
        "file_system": Field(
            StringSource, description="The storage account filesystem (aka container)"
        ),
        "overwrite": Field(bool, is_required=False, default_value=False),
    }
)
def adls2_file_cache(init_context):
    return ADLS2FileCache(
        storage_account=init_context.resource_config["storage_account"],
        file_system=init_context.resource_config["file_system"],
        prefix=init_context.resource_config["prefix"],
        credential=init_context.resource_config["credential"],
        overwrite=init_context.resource_config["overwrite"],
        # TODO: resource dependencies
    )

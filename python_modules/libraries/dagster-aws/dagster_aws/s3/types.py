from io import BytesIO


from dagster import check, Enum, EnumValue
from dagster.core.object_store import TypeStoragePlugin
from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile

S3ACL = Enum(
    'S3ACL',
    enum_values=[
        EnumValue('private'),
        EnumValue('public-read'),
        EnumValue('public-read-write'),
        EnumValue('authenticated-read'),
        EnumValue('aws-exec-read'),
        EnumValue('bucket-owner-read'),
        EnumValue('bucket-owner-full-control'),
    ],
)


class BytesIOS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, context, runtime_type, paths):
        if isinstance(obj, bytes):
            return super(BytesIOS3StoragePlugin, cls).set_object(
                object_store, obj, context, runtime_type, paths
            )
        elif isinstance(obj, BytesIO):
            return super(BytesIOS3StoragePlugin, cls).set_object(
                object_store, obj.read(), context, runtime_type, paths
            )
        else:
            check.invariant('Shouldn\'t be here')

    @classmethod
    def get_object(cls, object_store, context, runtime_type, paths):
        return BytesIO(
            super(BytesIOS3StoragePlugin, cls).get_object(
                object_store, context, runtime_type, paths
            )
        )


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(safe_isfile, value)

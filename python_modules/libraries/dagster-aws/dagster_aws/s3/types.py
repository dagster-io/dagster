from dagster import Enum, EnumValue
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


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(safe_isfile, value)

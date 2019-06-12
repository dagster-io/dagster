from dagster import Enum, EnumValue

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

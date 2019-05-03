from dagster import Dict, Field, Int, PermissiveDict, String

from .types import S3ACL


def put_object_configs():
    return Field(
        Dict(
            fields={
                'ACL': Field(
                    S3ACL, description='The canned ACL to apply to the object.', is_optional=True
                ),
                # Body will be set by the solid, not supplied in config
                'Bucket': Field(
                    String,
                    description='Name of the bucket to which the PUT operation was initiated.',
                    is_optional=False,
                ),
                'CacheControl': Field(
                    String,
                    description='Specifies caching behavior along the request/reply chain.',
                    is_optional=True,
                ),
                'ContentDisposition': Field(
                    String,
                    description='Specifies presentational information for the object.',
                    is_optional=True,
                ),
                'ContentEncoding': Field(
                    String,
                    description='''Specifies what content encodings have been applied to the object
                    and thus what decoding mechanisms must be applied to obtain the media-type
                    referenced by the Content-Type header field.''',
                    is_optional=True,
                ),
                'ContentLanguage': Field(
                    String, description='The language the content is in.', is_optional=True
                ),
                'ContentLength': Field(
                    Int,
                    description='''Size of the body in bytes. This parameter is useful when the size
                    of the body cannot be determined automatically.''',
                    is_optional=True,
                ),
                'ContentMD5': Field(
                    String,
                    description='''The base64-encoded 128-bit MD5 digest of the part data. This
                    parameter is auto-populated when using the command from the CLI''',
                    is_optional=True,
                ),
                'ContentType': Field(
                    String,
                    description='A standard MIME type describing the format of the object data.',
                    is_optional=True,
                ),
                # TODO: datetime object
                # # 'Expires': Field(datetime, description='The date and time at which the object is
                # no longer cacheable.', is_optional=True),
                'GrantFullControl': Field(
                    String,
                    description='''Gives the grantee READ, READ_ACP, and WRITE_ACP permissions on
                    the object.''',
                    is_optional=True,
                ),
                'GrantRead': Field(
                    String,
                    description='Allows grantee to read the object data and its metadata.',
                    is_optional=True,
                ),
                'GrantReadACP': Field(
                    String, description='Allows grantee to read the object ACL.', is_optional=True
                ),
                'GrantWriteACP': Field(
                    String,
                    description='Allows grantee to write the ACL for the applicable object.',
                    is_optional=True,
                ),
                'Key': Field(
                    String,
                    description='Object key for which the PUT operation was initiated.',
                    is_optional=False,
                ),
                'Metadata': Field(
                    PermissiveDict(),
                    description='A map of metadata to store with the object in S3.',
                    is_optional=True,
                ),
                'ServerSideEncryption': Field(
                    String,
                    description='''The Server-side encryption algorithm used when storing this
                    object in S3 (e.g., AES256, aws:kms).''',
                    is_optional=True,
                ),
                'StorageClass': Field(
                    String,
                    description='''The type of storage to use for the object. Defaults to
                    'STANDARD'.''',
                    is_optional=True,
                ),
                'WebsiteRedirectLocation': Field(
                    String,
                    description='''If the bucket is configured as a website, redirects requests for
                    this object to another object in the same bucket or to an external URL. Amazon
                    S3 stores the value of this header in the object metadata.''',
                    is_optional=True,
                ),
                'SSECustomerAlgorithm': Field(
                    String,
                    description='''Specifies the algorithm to use to when encrypting the object
                    (e.g., AES256).''',
                    is_optional=True,
                ),
                'SSECustomerKey': Field(
                    String,
                    description='''Specifies the customer-provided encryption key for Amazon S3 to
                    use in encrypting data. This value is used to store the object and then it is
                    discarded; Amazon does not store the encryption key. The key must be appropriate
                    for use with the algorithm specified in the
                    x-amz-server-side-encryption-customer-algorithm header.''',
                    is_optional=True,
                ),
                'SSECustomerKeyMD5': Field(
                    String,
                    description='''Specifies the 128-bit MD5 digest of the encryption key according
                    to RFC 1321. Amazon S3 uses this header for a message integrity check to ensure
                    the encryption key was transmitted without error.

                    Please note that this parameter is automatically populated if it is not
                    provided. Including this parameter is not required''',
                    is_optional=True,
                ),
                'SSEKMSKeyId': Field(
                    String,
                    description='''Specifies the AWS KMS key ID to use for object encryption. All
                    GET and PUT requests for an object protected by AWS KMS will fail if not made
                    via SSL or using SigV4. Documentation on configuring any of the officially
                    supported AWS SDKs and CLI can be found at
                    http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingAWSSDK.html#specify-signature-version''',
                    is_optional=True,
                ),
                'RequestPayer': Field(
                    String,
                    description='''Confirms that the requester knows that she or he will be charged
                    for the request. Bucket owners need not specify this parameter in their
                    requests. Documentation on downloading objects from requester pays buckets can
                    be found at
                    http://docs.aws.amazon.com/AmazonS3/latest/dev/ObjectsinRequesterPaysBuckets.html''',
                    is_optional=True,
                ),
                'Tagging': Field(
                    String,
                    description='''The tag-set for the object. The tag-set must be encoded as URL
                    Query parameters. (For example, "Key1=Value1")''',
                    is_optional=True,
                ),
                'ObjectLockMode': Field(
                    String,
                    description='The Object Lock mode that you want to apply to this object.',
                    is_optional=True,
                ),
                # TODO: datetime object 'ObjectLockRetainUntilDate': Field(datetime,
                # description='The date and time when you want this object\'s Object Lock to
                # expire.', is_optional=True),
                'ObjectLockLegalHoldStatus': Field(
                    String,
                    description='''The Legal Hold status that you want to apply to the specified
                    object.''',
                    is_optional=True,
                ),
            }
        )
    )

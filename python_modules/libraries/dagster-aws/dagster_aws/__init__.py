from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_aws.components import (
    AthenaClientResourceComponent as AthenaClientResourceComponent,
    AthenaCredentialsComponent as AthenaCredentialsComponent,
    Boto3CredentialsComponent as Boto3CredentialsComponent,
    ECRPublicResourceComponent as ECRPublicResourceComponent,
    ParameterStoreResourceComponent as ParameterStoreResourceComponent,
    RDSResourceComponent as RDSResourceComponent,
    S3CredentialsComponent as S3CredentialsComponent,
    S3FileManagerResourceComponent as S3FileManagerResourceComponent,
    S3ResourceComponent as S3ResourceComponent,
    SecretsManagerResourceComponent as SecretsManagerResourceComponent,
    SecretsManagerSecretsResourceComponent as SecretsManagerSecretsResourceComponent,
    SSMResourceComponent as SSMResourceComponent,
)
from dagster_aws.version import __version__

DagsterLibraryRegistry.register("dagster-aws", __version__)

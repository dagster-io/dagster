from dagster_aws.components.athena import (
    AthenaClientResourceComponent as AthenaClientResourceComponent,
)
from dagster_aws.components.credentials import (
    AthenaCredentialsComponent as AthenaCredentialsComponent,
    Boto3CredentialsComponent as Boto3CredentialsComponent,
    S3CredentialsComponent as S3CredentialsComponent,
)
from dagster_aws.components.ecr import ECRPublicResourceComponent as ECRPublicResourceComponent
from dagster_aws.components.rds import RDSResourceComponent as RDSResourceComponent
from dagster_aws.components.s3 import (
    S3FileManagerResourceComponent as S3FileManagerResourceComponent,
    S3ResourceComponent as S3ResourceComponent,
)
from dagster_aws.components.secretsmanager import (
    SecretsManagerResourceComponent as SecretsManagerResourceComponent,
    SecretsManagerSecretsResourceComponent as SecretsManagerSecretsResourceComponent,
)
from dagster_aws.components.ssm import (
    ParameterStoreResourceComponent as ParameterStoreResourceComponent,
    SSMResourceComponent as SSMResourceComponent,
)

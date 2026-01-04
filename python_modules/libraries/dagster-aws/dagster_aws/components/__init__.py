from dagster_aws.components.athena import (
    AthenaClientResourceComponent as AthenaClientResourceComponent,
)
from dagster_aws.components.credentials import (
    AthenaCredentialsComponent as AthenaCredentialsComponent,
    Boto3CredentialsComponent as Boto3CredentialsComponent,
    RedshiftCredentialsComponent as RedshiftCredentialsComponent,
    S3CredentialsComponent as S3CredentialsComponent,
)
from dagster_aws.components.rds import RDSResourceComponent as RDSResourceComponent
from dagster_aws.components.redshift import (
    RedshiftClientResourceComponent as RedshiftClientResourceComponent,
)
from dagster_aws.components.s3 import (
    S3FileManagerComponent as S3FileManagerComponent,
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

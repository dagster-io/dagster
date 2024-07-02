from .secrets import (
    get_tagged_secrets as get_tagged_secrets,
    get_secrets_from_arns as get_secrets_from_arns,
)
from .resources import (
    SecretsManagerResource as SecretsManagerResource,
    SecretsManagerSecretsResource as SecretsManagerSecretsResource,
    secretsmanager_resource as secretsmanager_resource,
    secretsmanager_secrets_resource as secretsmanager_secrets_resource,
)

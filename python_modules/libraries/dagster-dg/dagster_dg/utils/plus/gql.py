FULL_DEPLOYMENTS_QUERY = """
query CliDeploymentsQuery {
    fullDeployments {
        deploymentName
        deploymentId
        deploymentType
    }
}
"""

SECRETS_QUERY = """
query AllSecretsQuery($onlyViewable: Boolean, $scopes: SecretScopesInput) {
  secretsOrError(onlyViewable: $onlyViewable, scopes: $scopes) {
    __typename
    ... on Secrets {
      secrets {
        localDeploymentScope
        secretName
        secretValue
        locationNames
      }
    }
    ... on UnauthorizedError {
        message
    }
    ... on PythonError {
        message
        stack
    }
  }
}
"""


SECRETS_QUERY = """
{
	secretsOrError {
    __typename
    ... on Secrets {
      secrets {
        id
        localDeploymentScope
        fullDeploymentScope
        allBranchDeploymentsScope
        specificBranchDeploymentScope
        secretName
        secretValue
        locationNames
      }
    }
    ... on UnauthorizedError {
        message
    }
    ... on PythonError {
        message
        stack
    }
  }
}
"""


CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION = """
    mutation CreateOrUpdateSecretForScopes($secretName: String!, $secretValue: String!, $scopes: SecretScopesInput!, $locationName: String) {
        createOrUpdateSecretForScopes(secretName: $secretName, secretValue: $secretValue, scopes: $scopes, locationName: $locationName) {
            __typename
            ... on CreateOrUpdateSecretSuccess {
                secret {
                    id
                    secretName
                    secretValue
                }
            }
            ...on SecretAlreadyExistsError {
                message
            }
            ...on TooManySecretsError {
                message
            }
            ...on InvalidSecretInputError {
                message
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""

GET_SECRETS_FOR_SCOPES_QUERY = """
query SecretsForScopesQuery($locationName: String, $scopes: SecretScopesInput!, $secretName: String!) {
    secretsOrError(locationName: $locationName, scopes: $scopes, secretName: $secretName) {
        __typename
        ... on Secrets {
            secrets {
                id
                secretName
                secretValue

                updatedBy {
                    email
                }

                updateTimestamp

                locationNames

                fullDeploymentScope
                allBranchDeploymentsScope
                specificBranchDeploymentScope
                localDeploymentScope
                canViewSecretValue
                canEditSecret
            }
        }
        ...on UnauthorizedError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""

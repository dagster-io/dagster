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

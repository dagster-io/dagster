FULL_DEPLOYMENTS_QUERY = """
query CliDeploymentsQuery {
    fullDeployments {
        deploymentName
        deploymentId
        deploymentType
    }
}
"""

LOCAL_SECRETS_FILE_QUERY = """
{
	viewableLocalSecretsOrError {
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

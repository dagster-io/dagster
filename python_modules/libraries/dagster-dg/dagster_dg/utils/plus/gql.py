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
	secretsOrError {
    __typename
    ... on Secrets {
      secrets {
        localDeploymentScope
        secretName
        secretValue
        locationNames
      }
    }
  }
}
"""

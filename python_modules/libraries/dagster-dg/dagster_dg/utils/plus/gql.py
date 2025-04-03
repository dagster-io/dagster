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

AGENT_TOKENS_QUERY = """
query AgentTokensQuery {
    agentTokensOrError {
        __typename
        ... on DagsterCloudAgentTokens {
            tokens {
                id
                description
                token
                revoked
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

CREATE_AGENT_TOKEN_MUTATION = """
mutation CreateAgentTokenMutation($description: String!) {
    createAgentToken(description: $description) {
        __typename
        ... on DagsterCloudAgentToken {
            token
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

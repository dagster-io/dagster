GET_USER_CLOUD_REQUESTS_QUERY = """
    mutation GetUserCloudRequests($forBranchDeployments: Boolean $forFullDeployments: [String!], $limit: Int, $agentQueues: [String]) {
        userCloudAgent {
            popUserCloudAgentRequests(limit: $limit, forBranchDeployments: $forBranchDeployments, forFullDeployments: $forFullDeployments, agentQueues: $agentQueues) {
                requestId
                requestApi
                requestBody
                deploymentName
                isBranchDeployment
            }
        }
    }

"""

DEPLOYMENTS_QUERY = """
    query Deployments($deploymentNames: [String!]!) {
        deployments(deploymentNames: $deploymentNames) {
            deploymentName
        }
    }
"""

WORKSPACE_ENTRIES_QUERY = """
    query WorkspaceEntries($deploymentNames: [String!]!, $includeAllServerlessDeployments: Boolean!, $agentQueues: [String]) {
        deployments(deploymentNames: $deploymentNames, includeAllServerlessDeployments: $includeAllServerlessDeployments) {
            deploymentName
            isBranchDeployment
            workspaceEntries(agentQueues: $agentQueues) {
                locationName
                serializedDeploymentMetadata
                hasOutdatedData
                hasLoadError
                metadataTimestamp
            }
        }
    }
"""


ADD_AGENT_HEARTBEATS_MUTATION = """
    mutation AddAgentHeartbeats($serializedAgentHeartbeats: [AgentHeartbeatInput!], $serializedErrors: [String!]) {
        userCloudAgent {
            addAgentHeartbeats (serializedAgentHeartbeats: $serializedAgentHeartbeats, serializedErrors: $serializedErrors) {
                ok
            }
        }
    }
"""

GET_AGENTS_QUERY = """
    query Agents($heartbeatedSince: Float) {
        agents(heartbeatedSince: $heartbeatedSince) {
            id
            status
        }
    }
"""

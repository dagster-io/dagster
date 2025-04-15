from enum import Enum


class DgPlusDeploymentType(Enum):
    FULL_DEPLOYMENT = "full"
    BRANCH_DEPLOYMENT = "branch"


class DgPlusAgentType(Enum):
    SERVERLESS = "serverless"
    HYBRID = "hybrid"

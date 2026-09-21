import uuid

from dagster._core.errors import DagsterInvariantViolationError


def get_hardcoded_test_agent_token(organization_name) -> str:
    return f"agent:{organization_name}:hardcoded"


def get_hardcoded_test_user_token(organization_name, user_name) -> str:
    return f"user:{organization_name}:{user_name}"


def get_organization_public_id_from_api_token(api_token: str) -> str | None:
    split_token = api_token.split(":")
    if len(split_token) != 4:
        raise Exception("Could not derive organization from api token")

    return split_token[2]


def decode_region_from_uuid(regional_token: str) -> str | None:
    try:
        regional_uuid = uuid.UUID(regional_token)
    except ValueError:
        # if it's not an actual uuid, we can't decode region
        return None

    # custom uuids contain region subdomains in the first 2 bytes
    if regional_uuid.version != 8 or regional_uuid.variant != uuid.RFC_4122:
        return None

    uuid_bytes = regional_uuid.bytes
    return uuid_bytes[:2].decode("ascii")


def decode_agent_token(agent_token: str) -> tuple[str | None, str | None]:
    split_token = agent_token.split(":")

    # Legacy agent token format - organization must be specified in dagster.yaml
    if len(split_token) == 1:
        return None, None

    token_type, *token = split_token

    if token_type == "user":
        raise DagsterInvariantViolationError(
            "Agent was configured with a user token, but agents can only authenticate with "
            "Dagster Cloud when configured with an agent token. "
            "Generate a new agent token in Dagster Cloud."
        )

    # token format: agent:<org>:<uuid>
    organization, uuid_str = token
    return organization, decode_region_from_uuid(uuid_str)

import hashlib
import re

from azure.mgmt.appcontainers.models import RegistryCredentials

# Container Apps resource names: at most 32 chars of lowercase alphanumerics and hyphens,
# starting and ending with an alphanumeric.
_ACA_NAME_MAX_LENGTH = 32
_ACA_NAME_REPLACE_RE = re.compile(r"[^a-z0-9-]+")


def sanitize_aca_name(raw: str) -> str:
    """Return a valid Container Apps resource name derived from `raw`.

    Names over the limit are truncated and given a hash suffix so distinct inputs stay distinct.
    """
    lowered = _ACA_NAME_REPLACE_RE.sub("-", raw.lower()).strip("-")
    if len(lowered) <= _ACA_NAME_MAX_LENGTH:
        return lowered

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:7]
    prefix = lowered[: _ACA_NAME_MAX_LENGTH - 8].rstrip("-")
    return f"{prefix}-{digest}"


def build_acr_registry_credentials(
    identity_id: str | None, image: str
) -> list[RegistryCredentials] | None:
    """Return managed-identity pull credentials for an Azure Container Registry image, else None."""
    if not identity_id or "/" not in image:
        return None
    image_host = image.split("/", 1)[0]
    if not image_host.endswith(".azurecr.io"):
        return None
    return [RegistryCredentials(server=image_host, identity=identity_id)]

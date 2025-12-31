import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, Optional

from dagster_shared.merger import deep_merge_dicts
from dagster_shared.utils.config import get_dg_config_path, load_config, write_config

DEFAULT_CLOUD_CLI_FOLDER = os.path.join(os.path.expanduser("~"), ".dagster_cloud_cli")
DEFAULT_CLOUD_CLI_CONFIG = os.path.join(DEFAULT_CLOUD_CLI_FOLDER, "config")


class DagsterPlusConfigInfo(NamedTuple):
    path: Path
    raw_config: Mapping[str, Any]
    plus_config: Mapping[str, Any]
    is_dg_config: bool


DAGSTER_CLOUD_BASE_URL = "https://dagster.cloud"

# Supported regions and their base URLs
DAGSTER_CLOUD_REGIONS = {
    "us": "https://dagster.cloud",
    "eu": "https://eu.dagster.cloud",
}


def get_dagster_cloud_base_url_for_region(region: Optional[str]) -> str:
    """Get the Dagster Cloud base URL for a given region.

    Args:
        region: The region identifier (e.g., "us", "eu"). If None, defaults to "us".

    Returns:
        The base URL for the specified region.
    """
    if region is None:
        return DAGSTER_CLOUD_BASE_URL
    region_lower = region.lower()
    if region_lower not in DAGSTER_CLOUD_REGIONS:
        raise ValueError(
            f"Unknown region: {region}. Supported regions are: {', '.join(DAGSTER_CLOUD_REGIONS.keys())}"
        )
    return DAGSTER_CLOUD_REGIONS[region_lower]


def get_region_from_url(url: Optional[str]) -> Optional[str]:
    """Derive region from a Dagster Cloud URL.

    Args:
        url: A Dagster Cloud URL (e.g., "https://eu.dagster.cloud")

    Returns:
        The region identifier ("eu") or None for default US region.
    """
    if url and "eu.dagster.cloud" in url:
        return "eu"
    return None


def _get_dagster_plus_config_path_and_raw_config() -> Optional[DagsterPlusConfigInfo]:
    cloud_config_path = get_dagster_cloud_cli_config_path()
    dg_config_path = get_dg_config_path()

    dg_config = load_config(dg_config_path) if dg_config_path.exists() else None
    dg_plus_config = dg_config.get("cli", {}).get("plus", {}) if dg_config else None
    cloud_config = load_config(cloud_config_path) if cloud_config_path.exists() else None

    if dg_plus_config and cloud_config:
        raise Exception(
            f"Found Dagster Plus config in both {dg_config_path} and {cloud_config_path}. Please consolidate your config files."
        )

    if cloud_config is not None:
        return DagsterPlusConfigInfo(
            cloud_config_path, cloud_config, cloud_config, is_dg_config=False
        )
    elif dg_config is not None and dg_plus_config is not None:
        return DagsterPlusConfigInfo(dg_config_path, dg_config, dg_plus_config, is_dg_config=True)

    return None


@dataclass()
class DagsterPlusCliConfig:
    url: Optional[str] = None
    organization: Optional[str] = None
    default_deployment: Optional[str] = None
    user_token: Optional[str] = None
    agent_timeout: Optional[int] = None

    def has_any_configuration(self) -> bool:
        return any(self.__dict__.values())

    @staticmethod
    def exists() -> bool:
        return _get_dagster_plus_config_path_and_raw_config() is not None

    @classmethod
    def get(cls) -> "DagsterPlusCliConfig":
        result = _get_dagster_plus_config_path_and_raw_config()
        if result is None:
            raise Exception("No Dagster Plus config found")
        _, _, raw_plus_config, _ = result
        return cls(**raw_plus_config)

    @classmethod
    def create_for_deployment(
        cls,
        deployment: Optional[str],
        organization: Optional[str] = None,
        user_token: Optional[str] = None,
    ) -> "DagsterPlusCliConfig":
        """Create a DagsterPlusCliConfig instance for deployment-scoped operations.

        Args:
            deployment: The deployment name to target
            organization: Organization name (if None, will try to load from existing config)
            user_token: User token (if None, will try to load from existing config)
        """
        # Try to get base config if it exists, but don't require it
        base_config = {}
        if cls.exists():
            try:
                base_config = cls.get().__dict__
            except Exception:
                # If config exists but is invalid, start with empty base
                pass

        return cls(
            url=base_config.get("url"),
            organization=organization or base_config.get("organization"),
            default_deployment=deployment,  # Override with specific deployment
            user_token=user_token or base_config.get("user_token"),
            agent_timeout=base_config.get("agent_timeout"),
        )

    @classmethod
    def create_for_organization(
        cls, organization: Optional[str] = None, user_token: Optional[str] = None
    ) -> "DagsterPlusCliConfig":
        """Create a DagsterPlusCliConfig instance for organization-scoped operations.

        Args:
            organization: Organization name (if None, will try to load from existing config)
            user_token: User token (if None, will try to load from existing config)
        """
        # Try to get base config if it exists, but don't require it
        base_config = {}
        if cls.exists():
            try:
                base_config = cls.get().__dict__
            except Exception:
                # If config exists but is invalid, start with empty base
                pass

        return cls(
            url=base_config.get("url"),
            organization=organization or base_config.get("organization"),
            default_deployment=None,  # No deployment for organization-scoped operations
            user_token=user_token or base_config.get("user_token"),
            agent_timeout=base_config.get("agent_timeout"),
        )

    def write(self):
        existing_config = _get_dagster_plus_config_path_and_raw_config()
        if existing_config is None:
            config_path = get_dg_config_path()
            raw_config = {}
            is_dg_config = True
        else:
            config_path, raw_config, _, is_dg_config = existing_config

        config_to_apply = {k: v for k, v in self.__dict__.items() if v is not None}
        if is_dg_config:
            config_to_apply = {"cli": {"plus": config_to_apply}}

        config_dict = deep_merge_dicts(raw_config, config_to_apply)
        write_config(config_path, config_dict)

    @property
    def organization_url(self) -> str:
        if not self.organization:
            raise Exception("Organization not set")
        if self.url is None:
            return f"{DAGSTER_CLOUD_BASE_URL}/{self.organization}"
        return f"{self.url}/{self.organization}"


def get_dagster_cloud_cli_config_path() -> Path:
    return Path(os.getenv("DAGSTER_CLOUD_CLI_CONFIG", DEFAULT_CLOUD_CLI_CONFIG))

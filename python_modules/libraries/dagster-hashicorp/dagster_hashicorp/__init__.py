from dagster.core.utils import check_dagster_package_version

from .vault import Vault, vault_resource
from .version import __version__

check_dagster_package_version("dagster-hashicorp", __version__)

__all__ = [
    "vault_resource",
    "Vault",
]

# SLA definition stuff
from collections.abc import Mapping
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSeverity
from dagster._core.definitions.events import AssetKey, MetadataValue
from dagster._core.definitions.metadata import normalize_metadata
from dagster._serdes import whitelist_for_serdes

class SlaViolating():
    pass

class SlaPassing():
    pass
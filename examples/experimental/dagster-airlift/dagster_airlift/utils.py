import os
from pathlib import Path
from typing import Optional

DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR = "DAGSTER_AIRLIFT_MIGRATION_STATE_DIR"
from typing import Generic, List, Mapping, TypeVar

from dagster._record import record
from dagster._serdes import whitelist_for_serdes


def get_local_migration_state_dir() -> Optional[Path]:
    migration_dir = os.getenv(DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR)
    return Path(migration_dir) if migration_dir else None


TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


@whitelist_for_serdes
@record
class DictItem(Generic[TKey, TValue]):
    key: TKey
    value: TValue


def items_from_dict(d: Mapping[TKey, TValue]) -> List[DictItem[TKey, TValue]]:
    return [DictItem(key=k, value=v) for k, v in d.items()]


def dict_from_items(items: List[DictItem[TKey, TValue]]) -> Mapping[TKey, TValue]:
    return {item.key: item.value for item in items}

from typing import AbstractSet

from dagster import AssetSpec

from dagster_airlift.core.utils import AssetSpecPredicate


def dag_name_in(names: AbstractSet[str]) -> AssetSpecPredicate:
    def _dag_name_in(spec: AssetSpec) -> bool:
        return spec.metadata["Dag ID"] in names

    return _dag_name_in

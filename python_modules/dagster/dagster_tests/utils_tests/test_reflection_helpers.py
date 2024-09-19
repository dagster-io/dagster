from dagster import AssetsDefinition
from dagster._utils.internal_init import IHasInternalInit
from dagster._utils.test import get_all_direct_subclasses_of_marker


def test_ihas_init_reflection_helper() -> None:
    all_types = get_all_direct_subclasses_of_marker(IHasInternalInit)
    assert AssetsDefinition in all_types

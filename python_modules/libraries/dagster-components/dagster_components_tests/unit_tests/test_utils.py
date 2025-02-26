import pytest
from dagster_components.utils import get_wrapped_translator_class
from dagster_dbt import DagsterDbtTranslator
from dagster_sling import DagsterSlingTranslator

EXCLUDED_METHODS = [
    "get_auto_materialize_policy",  # Not supported by asset_attributes
    "get_asset_spec",  # Not supported by asset_attributes
    "get_freshness_policy",  # Not supported by asset_attributes
    "get_partition_mapping",  # Not supported by asset_attributes
    "get_partitions_def",  # Not supported by asset_attributes
    "get_kinds",  # included in get_tags
    #
    # Misc internal methods
    "settings",
    "sanitize_stream_name",
    "target",
    "target_prefix",
]


@pytest.mark.parametrize("translator_type", [DagsterDbtTranslator, DagsterSlingTranslator])
def test_get_wrapped_translator_class(translator_type):
    wrapped = get_wrapped_translator_class(translator_type)

    # Ensure all translator methods are properly specified in the wrapped class,
    # so user input actually flows through to the generated assets.
    for method in dir(translator_type):
        if method.startswith("_") or method in EXCLUDED_METHODS:
            continue
        assert method in dir(wrapped)
        assert getattr(wrapped, method) != getattr(
            translator_type, method
        ), f"{method} is not overridden by get_wrapped_translator_class"

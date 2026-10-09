import dagster as dg
import pytest
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.storage.partition_status_cache import (
    DYNAMIC_PARTITION_VALIDATION_LOOKUP_LIMIT,
    get_validated_partition_keys,
)

from dagster_tests.storage_tests.utils.partition_status_cache import TestPartitionStatusCache


class TestSqlPartitionStatusCache(TestPartitionStatusCache):
    @pytest.fixture
    def instance(self):
        with dg.instance_for_test() as the_instance:
            yield the_instance


def test_validating_dynamic_partition_keys_does_not_load_full_partition_set(monkeypatch):
    partitions_def = dg.DynamicPartitionsDefinition(name="foo")
    all_keys = [f"key_{i}" for i in range(DYNAMIC_PARTITION_VALIDATION_LOOKUP_LIMIT * 2)]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", all_keys)

        full_fetches: list[str] = []
        original_get = instance.get_dynamic_partitions

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)

        with partition_loading_context(dynamic_partitions_store=instance):
            # a handful of candidates is validated with per-key lookups
            assert get_validated_partition_keys(partitions_def, {"key_1", "key_2", "nope"}) == {
                "key_1",
                "key_2",
            }
            assert full_fetches == []

            # validating more keys than the lookup limit is cheaper as one bulk fetch
            candidates = {*all_keys, "nope"}
            assert get_validated_partition_keys(partitions_def, candidates) == set(all_keys)
            assert full_fetches == ["foo"]


def test_validating_partition_fn_keys_calls_the_function_once():
    calls = []

    def _partition_fn(_current_time):
        calls.append(1)
        return ["a", "b", "c"]

    partitions_def = dg.DynamicPartitionsDefinition(_partition_fn)

    # a partition_fn definition re-runs the user's function on every membership check, so it must
    # stay on the bulk path no matter how few keys are being validated
    assert get_validated_partition_keys(partitions_def, {"a", "nope"}) == {"a"}
    assert len(calls) == 1

import dagster as dg
import pytest
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.storage.partition_status_cache import get_validated_partition_keys

from dagster_tests.storage_tests.utils.partition_status_cache import TestPartitionStatusCache


class TestSqlPartitionStatusCache(TestPartitionStatusCache):
    @pytest.fixture
    def instance(self):
        with dg.instance_for_test() as the_instance:
            yield the_instance


def test_validating_dynamic_partition_keys_does_not_load_full_partition_set(monkeypatch):
    partitions_def = dg.DynamicPartitionsDefinition(name="foo")
    all_keys = [f"key_{i}" for i in range(500)]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", all_keys)

        full_fetches: list[str] = []
        membership_lookups: list[list[str]] = []
        original_get = instance.get_dynamic_partitions
        original_existing = instance.get_existing_dynamic_partitions

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        def _spy_existing(partitions_def_name, partition_keys):
            membership_lookups.append(sorted(partition_keys))
            return original_existing(partitions_def_name, partition_keys)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)
        monkeypatch.setattr(instance, "get_existing_dynamic_partitions", _spy_existing)

        with partition_loading_context(dynamic_partitions_store=instance):
            assert get_validated_partition_keys(partitions_def, {"key_1", "key_2", "nope"}) == {
                "key_1",
                "key_2",
            }
            # validating every key is still one batched lookup, not a fetch of the whole key set
            assert get_validated_partition_keys(partitions_def, {*all_keys, "nope"}) == set(
                all_keys
            )

        assert full_fetches == []
        assert membership_lookups[0] == ["key_1", "key_2", "nope"]
        assert len(membership_lookups) == 2


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

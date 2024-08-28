import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Set

import pytest
from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    AutomationCondition,
    BackfillPolicy,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    Definitions,
    DependencyDefinition,
    DimensionPartitionMapping,
    FreshnessPolicy,
    Jitter,
    LastPartitionMapping,
    MultiPartitionMapping,
    NodeInvocation,
    OpDefinition,
    PartitionMapping,
    PartitionsDefinition,
    RetryPolicy,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
    materialize,
)
from dagster._core.definitions.tags import StorageKindTagSet
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._core.types.dagster_type import DagsterType
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_specs import build_dbt_asset_specs
from dagster_dbt.asset_utils import DUPLICATE_ASSET_KEY_ERROR_MESSAGE
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dbt.version import __version__ as dbt_version
from packaging import version

from dagster_dbt_tests.dbt_projects import (
    test_dbt_alias_path,
    test_dbt_model_versions_path,
    test_dbt_python_interleaving_path,
    test_dbt_semantic_models_path,
    test_dbt_unit_tests_path,
    test_meta_config_path,
)


def test_manifest_argument(
    test_jaffle_shop_manifest_path: Path, test_jaffle_shop_manifest: Dict[str, Any]
) -> None:
    for manifest_param in [
        test_jaffle_shop_manifest,
        test_jaffle_shop_manifest_path,
        os.fspath(test_jaffle_shop_manifest_path),
    ]:

        @dbt_assets(manifest=manifest_param)
        def my_dbt_assets(): ...

        assert my_dbt_assets.keys == {
            AssetKey(key)
            for key in {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            }
        }


@pytest.mark.parametrize(
    ["select", "exclude", "expected_dbt_resource_names"],
    [
        (
            None,
            None,
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers stg_customers",
            None,
            {
                "raw_customers",
                "stg_customers",
            },
        ),
        (
            "raw_customers+",
            None,
            {
                "raw_customers",
                "stg_customers",
                "customers",
            },
        ),
        (
            "resource_type:model",
            None,
            {
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers+,resource_type:model",
            None,
            {
                "stg_customers",
                "customers",
            },
        ),
        (
            None,
            "orders",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
            },
        ),
        (
            None,
            "raw_customers+",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "orders",
            },
        ),
        (
            None,
            "raw_customers stg_customers",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            None,
            "resource_type:model",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
            },
        ),
        (
            None,
            "tag:does-not-exist",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
    ],
    ids=[
        "--select fqn:*",
        "--select raw_customers stg_customers",
        "--select raw_customers+",
        "--select resource_type:model",
        "--select raw_customers+,resource_type:model",
        "--exclude orders",
        "--exclude raw_customers+",
        "--exclude raw_customers stg_customers",
        "--exclude resource_type:model",
        "--exclude tag:does-not-exist",
    ],
)
def test_selections(
    test_jaffle_shop_manifest: Dict[str, Any],
    select: Optional[str],
    exclude: Optional[str],
    expected_dbt_resource_names: Set[str],
) -> None:
    select = select or "fqn:*"

    expected_asset_keys = {AssetKey(key) for key in expected_dbt_resource_names}
    expected_specs = build_dbt_asset_specs(
        manifest=test_jaffle_shop_manifest,
        select=select,
        exclude=exclude,
    )

    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        select=select,
        exclude=exclude,
    )
    def my_dbt_assets(): ...

    assert len(my_dbt_assets.keys) == len(expected_specs)
    assert my_dbt_assets.keys == {spec.key for spec in expected_specs}
    assert my_dbt_assets.keys == expected_asset_keys
    assert my_dbt_assets.op.tags.get("dagster_dbt/select") == select
    assert my_dbt_assets.op.tags.get("dagster_dbt/exclude") == exclude


@pytest.mark.parametrize("name", [None, "custom"])
def test_with_custom_name(test_jaffle_shop_manifest: Dict[str, Any], name: Optional[str]) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest, name=name)
    def my_dbt_assets(): ...

    expected_name = name or "my_dbt_assets"

    assert my_dbt_assets.op.name == expected_name


@pytest.mark.parametrize(
    "partitions_def", [None, DailyPartitionsDefinition(start_date="2023-01-01")]
)
def test_partitions_def(
    test_jaffle_shop_manifest: Dict[str, Any], partitions_def: Optional[PartitionsDefinition]
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest, partitions_def=partitions_def)
    def my_dbt_assets(): ...

    assert my_dbt_assets.partitions_def == partitions_def


@pytest.mark.parametrize("io_manager_key", [None, "my_io_manager_key"])
def test_io_manager_key(
    test_jaffle_shop_manifest: Dict[str, Any], io_manager_key: Optional[str]
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest, io_manager_key=io_manager_key)
    def my_dbt_assets(): ...

    expected_io_manager_key = DEFAULT_IO_MANAGER_KEY if io_manager_key is None else io_manager_key

    for output_def in my_dbt_assets.node_def.output_defs:
        if output_def.name in my_dbt_assets.keys_by_output_name:
            assert output_def.io_manager_key == expected_io_manager_key
        else:  # asset checks don't use io managers
            assert output_def.name in my_dbt_assets.check_specs_by_output_name
            assert output_def.io_manager_key == DEFAULT_IO_MANAGER_KEY


@pytest.mark.parametrize(
    ["partitions_def", "backfill_policy", "expected_backfill_policy"],
    [
        (
            DailyPartitionsDefinition(start_date="2023-01-01"),
            BackfillPolicy.multi_run(),
            BackfillPolicy.multi_run(),
        ),
        (
            DailyPartitionsDefinition(start_date="2023-01-01"),
            None,
            BackfillPolicy.single_run(),
        ),
        (
            StaticPartitionsDefinition(partition_keys=["A", "B"]),
            None,
            None,
        ),
        (
            StaticPartitionsDefinition(partition_keys=["A", "B"]),
            BackfillPolicy.single_run(),
            BackfillPolicy.single_run(),
        ),
    ],
    ids=[
        "use explicit backfill policy for time window",
        "time window defaults to single run",
        "non time window has no default backfill policy",
        "non time window backfill policy is respected",
    ],
)
def test_backfill_policy(
    test_jaffle_shop_manifest: Dict[str, Any],
    partitions_def: PartitionsDefinition,
    backfill_policy: BackfillPolicy,
    expected_backfill_policy: BackfillPolicy,
) -> None:
    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_freshness_policy(self, _: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
            # Disable freshness policies when using static partitions
            return None

    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        partitions_def=partitions_def,
        backfill_policy=backfill_policy,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(): ...

    assert my_dbt_assets.backfill_policy == expected_backfill_policy


@pytest.mark.parametrize(
    "retry_policy",
    [
        None,
        RetryPolicy(max_retries=1),
        RetryPolicy(max_retries=2, delay=1, jitter=Jitter.FULL),
    ],
    ids=[
        "no retry policy",
        "retry policy",
        "retry policy with jitter",
    ],
)
def test_retry_policy(
    test_jaffle_shop_manifest: Dict[str, Any],
    retry_policy: Optional[RetryPolicy],
) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        retry_policy=retry_policy,
    )
    def my_dbt_assets(): ...

    assert isinstance(my_dbt_assets.node_def, OpDefinition)
    assert my_dbt_assets.node_def.retry_policy == retry_policy


def test_op_tags(test_jaffle_shop_manifest: Dict[str, Any]):
    op_tags = {"a": "b", "c": "d"}

    @dbt_assets(manifest=test_jaffle_shop_manifest, op_tags=op_tags)
    def my_dbt_assets(): ...

    assert my_dbt_assets.op.tags == {
        **op_tags,
        COMPUTE_KIND_TAG: "dbt",
        "dagster_dbt/select": "fqn:*",
    }

    @dbt_assets(manifest=test_jaffle_shop_manifest, op_tags=op_tags, select="raw_customers+")
    def my_dbt_assets_with_select(): ...

    assert my_dbt_assets_with_select.op.tags == {
        **op_tags,
        COMPUTE_KIND_TAG: "dbt",
        "dagster_dbt/select": "raw_customers+",
    }

    @dbt_assets(manifest=test_jaffle_shop_manifest, op_tags=op_tags, exclude="raw_customers+")
    def my_dbt_assets_with_exclude(): ...

    assert my_dbt_assets_with_exclude.op.tags == {
        **op_tags,
        COMPUTE_KIND_TAG: "dbt",
        "dagster_dbt/select": "fqn:*",
        "dagster_dbt/exclude": "raw_customers+",
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        op_tags=op_tags,
        select="raw_customers+",
        exclude="customers",
    )
    def my_dbt_assets_with_select_and_exclude(): ...

    assert my_dbt_assets_with_select_and_exclude.op.tags == {
        **op_tags,
        COMPUTE_KIND_TAG: "dbt",
        "dagster_dbt/select": "raw_customers+",
        "dagster_dbt/exclude": "customers",
    }

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "To specify a dbt selection, use the 'select' argument, not 'dagster_dbt/select'"
            " with op_tags"
        ),
    ):

        @dbt_assets(
            manifest=test_jaffle_shop_manifest,
            op_tags={"dagster_dbt/select": "raw_customers+"},
        )
        def select_tag(): ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "To specify a dbt exclusion, use the 'exclude' argument, not 'dagster_dbt/exclude'"
            " with op_tags"
        ),
    ):

        @dbt_assets(
            manifest=test_jaffle_shop_manifest,
            op_tags={"dagster_dbt/exclude": "raw_customers+"},
        )
        def exclude_tag(): ...


def test_with_asset_key_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            return super().get_asset_key(dbt_resource_props).with_prefix("prefix")

    expected_specs = build_dbt_asset_specs(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    assert len(my_dbt_assets.keys) == len(expected_specs)
    assert my_dbt_assets.keys == {spec.key for spec in expected_specs}
    assert my_dbt_assets.keys_by_input_name == {
        "__subset_input__model_jaffle_shop_stg_customers": AssetKey(["prefix", "stg_customers"]),
        "__subset_input__model_jaffle_shop_stg_orders": AssetKey(["prefix", "stg_orders"]),
        "__subset_input__model_jaffle_shop_stg_payments": AssetKey(["prefix", "stg_payments"]),
        "__subset_input__seed_jaffle_shop_raw_customers": AssetKey(["prefix", "raw_customers"]),
        "__subset_input__seed_jaffle_shop_raw_orders": AssetKey(["prefix", "raw_orders"]),
        "__subset_input__seed_jaffle_shop_raw_payments": AssetKey(["prefix", "raw_payments"]),
    }
    assert set(my_dbt_assets.keys_by_output_name.values()) == {
        AssetKey(["prefix", "raw_customers"]),
        AssetKey(["prefix", "raw_orders"]),
        AssetKey(["prefix", "raw_payments"]),
        AssetKey(["prefix", "stg_customers"]),
        AssetKey(["prefix", "stg_orders"]),
        AssetKey(["prefix", "stg_payments"]),
        AssetKey(["prefix", "customers"]),
        AssetKey(["prefix", "orders"]),
    }


@pytest.mark.parametrize(
    "partition_mapping",
    [
        None,
        LastPartitionMapping(),
        TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=StaticPartitionMapping({"a": "1", "b": "2", "c": "3"}),
                ),
                "weekly": DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=TimeWindowPartitionMapping(),
                ),
            }
        ),
    ],
)
def test_with_partition_mappings(
    test_meta_config_manifest: Dict[str, Any], partition_mapping: Optional[PartitionMapping]
) -> None:
    expected_self_dependency_partition_mapping = TimeWindowPartitionMapping(
        start_offset=-8, end_offset=-9
    )

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_partition_mapping(
            self,
            dbt_resource_props: Mapping[str, Any],
            dbt_parent_resource_props: Mapping[str, Any],
        ) -> Optional[PartitionMapping]:
            is_self_dependency = dbt_resource_props == dbt_parent_resource_props
            if is_self_dependency:
                return expected_self_dependency_partition_mapping

            return partition_mapping

    @dbt_assets(
        manifest=test_meta_config_manifest,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
        partitions_def=DailyPartitionsDefinition(start_date="2023-10-01"),
    )
    def my_dbt_assets(): ...

    dependencies_with_self_dependencies = {
        # Self dependency enabled with `+meta.dagster.has_self_dependency`
        AssetKey("customers"),
    }
    dependencies_without_self_dependencies = set(my_dbt_assets.dependency_keys).difference(
        my_dbt_assets.keys
    )

    assert dependencies_without_self_dependencies
    for input_asset_key in dependencies_without_self_dependencies:
        assert my_dbt_assets.get_partition_mapping(input_asset_key) == partition_mapping

    for self_dependency_asset_key in dependencies_with_self_dependencies:
        assert (
            my_dbt_assets.get_partition_mapping(self_dependency_asset_key)
            == expected_self_dependency_partition_mapping
        )


def test_with_description_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_description = "customized description"

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_description(self, _: Mapping[str, Any]) -> str:
            return expected_description

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    assert len(my_dbt_assets.descriptions_by_key) == len(expected_specs_by_key)
    for asset_key, description in my_dbt_assets.descriptions_by_key.items():
        assert description == expected_description
        assert expected_specs_by_key[asset_key].description == expected_description


def test_with_metadata_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_metadata = {"customized": "metadata"}

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_metadata(self, _: Mapping[str, Any]) -> Mapping[str, Any]:
            return expected_metadata

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for asset_key, metadata in my_dbt_assets.metadata_by_key.items():
        assert metadata["customized"] == "metadata"
        assert expected_specs_by_key[asset_key].metadata["customized"] == "metadata"


def test_with_tag_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_tags = {"customized": "tag"}

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_tags(self, _: Mapping[str, Any]) -> Mapping[str, str]:
            return expected_tags

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for asset_key, tags in my_dbt_assets.tags_by_key.items():
        assert tags["customized"] == "tag"
        assert expected_specs_by_key[asset_key].tags["customized"] == "tag"


def test_with_storage_kind_tag_override(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_specs_with_no_override_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_jaffle_shop_manifest)
    }

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets_no_override(): ...

    for asset_key, tags in my_dbt_assets_no_override.tags_by_key.items():
        assert tags["dagster/storage_kind"] == "duckdb"
        assert (
            expected_specs_with_no_override_by_key[asset_key].tags["dagster/storage_kind"]
            == "duckdb"
        )

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_tags(self, _: Mapping[str, Any]) -> Mapping[str, str]:
            return {**StorageKindTagSet(storage_kind="my_custom_storage_kind")}

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for asset_key, tags in my_dbt_assets.tags_by_key.items():
        assert tags["dagster/storage_kind"] == "my_custom_storage_kind"
        assert (
            expected_specs_by_key[asset_key].tags["dagster/storage_kind"]
            == "my_custom_storage_kind"
        )


def test_with_owner_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_owners = ["custom@custom.com"]

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_owners(self, _: Mapping[str, Any]) -> Optional[Sequence[str]]:
            return expected_owners

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for spec in my_dbt_assets.specs:
        assert spec.owners == expected_owners
        assert expected_specs_by_key[spec.key].owners == expected_owners


def test_with_group_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_group = "customized_group"

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_group_name(self, _: Mapping[str, Any]) -> Optional[str]:
            return expected_group

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(): ...

    for asset_key, group in my_dbt_assets.group_names_by_key.items():
        assert group == expected_group
        assert expected_specs_by_key[asset_key].group_name == expected_group


def test_with_freshness_policy_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_freshness_policy = FreshnessPolicy(maximum_lag_minutes=60)

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_freshness_policy(self, _: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
            return expected_freshness_policy

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for asset_key, freshness_policy in my_dbt_assets.freshness_policies_by_key.items():
        assert freshness_policy == expected_freshness_policy
        assert expected_specs_by_key[asset_key].freshness_policy == expected_freshness_policy


def test_with_auto_materialize_policy_replacements(
    test_jaffle_shop_manifest: Dict[str, Any],
) -> None:
    expected_auto_materialize_policy = AutoMaterializePolicy.eager()

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_auto_materialize_policy(
            self, _: Mapping[str, Any]
        ) -> Optional[AutoMaterializePolicy]:
            return expected_auto_materialize_policy

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for (
        asset_key,
        auto_materialize_policy,
    ) in my_dbt_assets.auto_materialize_policies_by_key.items():
        assert auto_materialize_policy == expected_auto_materialize_policy
        assert (
            expected_specs_by_key[asset_key].auto_materialize_policy
            == expected_auto_materialize_policy
        )


def test_with_automation_condition_replacements(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    expected_automation_condition = AutomationCondition.eager()

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_automation_condition(self, _: Mapping[str, Any]) -> Optional[AutomationCondition]:
            return expected_automation_condition

    expected_specs_by_key = {
        spec.key: spec
        for spec in build_dbt_asset_specs(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )
    def my_dbt_assets(): ...

    for asset_key, automation_condition in my_dbt_assets.automation_conditions_by_key.items():
        assert automation_condition == expected_automation_condition
        assert (
            expected_specs_by_key[asset_key].automation_condition == expected_automation_condition
        )


def test_dbt_meta_auto_materialize_policy(test_meta_config_manifest: Dict[str, Any]) -> None:
    expected_auto_materialize_policy = AutoMaterializePolicy.eager()
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_meta_config_manifest)
    }

    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    auto_materialize_policies = my_dbt_assets.auto_materialize_policies_by_key.items()
    assert auto_materialize_policies

    for asset_key, auto_materialize_policy in auto_materialize_policies:
        assert auto_materialize_policy == expected_auto_materialize_policy
        assert (
            expected_specs_by_key[asset_key].auto_materialize_policy
            == expected_auto_materialize_policy
        )


def test_dbt_meta_freshness_policy(test_meta_config_manifest: Dict[str, Any]) -> None:
    expected_freshness_policy = FreshnessPolicy(maximum_lag_minutes=60.0, cron_schedule="* * * * *")
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_meta_config_manifest)
    }

    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    freshness_policies = my_dbt_assets.freshness_policies_by_key.items()
    assert freshness_policies

    for asset_key, freshness_policy in freshness_policies:
        assert freshness_policy == expected_freshness_policy
        assert expected_specs_by_key[asset_key].freshness_policy == expected_freshness_policy


def test_dbt_meta_asset_key(test_meta_config_manifest: Dict[str, Any]) -> None:
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_meta_config_manifest)
    }

    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    # Assert that source asset keys are set properly.
    assert AssetKey(["customized", "source", "jaffle_shop", "main", "raw_customers"]) in set(
        my_dbt_assets.keys_by_input_name.values()
    )

    # Assert that models asset keys are set properly.
    assert {
        AssetKey(["customized", "staging", "customers"]),
        AssetKey(["customized", "staging", "orders"]),
        AssetKey(["customized", "staging", "payments"]),
    }.issubset(my_dbt_assets.keys)
    assert {
        AssetKey(["customized", "staging", "customers"]),
        AssetKey(["customized", "staging", "orders"]),
        AssetKey(["customized", "staging", "payments"]),
    }.issubset(expected_specs_by_key.keys())


def test_dbt_config_group(test_meta_config_manifest: Dict[str, Any]) -> None:
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_meta_config_manifest)
    }

    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    assert my_dbt_assets.group_names_by_key == {
        asset_key: spec.group_name or "default" for asset_key, spec in expected_specs_by_key.items()
    }
    assert my_dbt_assets.group_names_by_key == {
        AssetKey(["customers"]): "default",
        # If a model has a Dagster group name specified under `meta`, use that.
        AssetKey(["customized", "staging", "customers"]): "customized_dagster_group",
        # If a model has a dbt group name specified under `group`, use that.
        AssetKey(["customized", "staging", "orders"]): "customized_dbt_model_group",
        # If a model has both a Dagster group and dbt group, use the Dagster group.
        AssetKey(["customized", "staging", "payments"]): "customized_dagster_group",
        AssetKey(["orders"]): "default",
        AssetKey(["raw_customers"]): "customized_dbt_seed_group",
        AssetKey(["raw_orders"]): "customized_dbt_seed_group",
        AssetKey(["raw_payments"]): "customized_dbt_seed_group",
    }


def test_dbt_config_tags(test_meta_config_manifest: Dict[str, Any]) -> None:
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_meta_config_manifest)
    }

    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    assert expected_specs_by_key[AssetKey("customers")].tags == {
        "foo": "",
        "bar-baz": "",
        **StorageKindTagSet(storage_kind="duckdb"),
    }
    assert my_dbt_assets.tags_by_key[AssetKey("customers")] == {
        "foo": "",
        "bar-baz": "",
        **StorageKindTagSet(storage_kind="duckdb"),
    }
    for asset_key in my_dbt_assets.keys - {AssetKey("customers")}:
        assert my_dbt_assets.tags_by_key[asset_key] == {**StorageKindTagSet(storage_kind="duckdb")}
        assert expected_specs_by_key[asset_key].tags == {**StorageKindTagSet(storage_kind="duckdb")}


def test_dbt_meta_owners(test_meta_config_manifest: Dict[str, Any]) -> None:
    expected_dbt_model_owners = ["kafka@amerika.com"]
    expected_dbt_seed_owners = ["kafka@judgment.com"]
    expected_dagster_owners = ["kafka@castle.com"]
    expected_specs_by_key = {
        spec.key: spec for spec in build_dbt_asset_specs(manifest=test_meta_config_manifest)
    }

    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    owners_by_key = {spec.key: spec.owners for spec in my_dbt_assets.specs}
    assert owners_by_key == {
        asset_key: spec.owners for asset_key, spec in expected_specs_by_key.items()
    }
    assert owners_by_key == {
        AssetKey(["customers"]): [],
        # If a model has Dagster owners specified under `meta`, use that.
        AssetKey(["customized", "staging", "customers"]): [],
        # If a model has a dbt owner specified under `group`, use that.
        AssetKey(["customized", "staging", "orders"]): expected_dbt_model_owners,
        # If a model has both Dagster owners and a dbt owner, use the Dagster owner.
        AssetKey(["customized", "staging", "payments"]): expected_dagster_owners,
        AssetKey(["orders"]): [],
        AssetKey(["raw_customers"]): expected_dbt_seed_owners,
        AssetKey(["raw_orders"]): expected_dbt_seed_owners,
        AssetKey(["raw_payments"]): expected_dbt_seed_owners,
    }


def test_dbt_with_downstream_asset_via_definition(test_meta_config_manifest: Dict[str, Any]):
    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    @asset(deps=[my_dbt_assets])
    def downstream_of_dbt():
        return None

    assert len(list(downstream_of_dbt.input_names)) == 8
    for input_name in downstream_of_dbt.input_names:
        input_dagster_type = downstream_of_dbt.op.ins[input_name].dagster_type

        assert isinstance(input_dagster_type, DagsterType) and input_dagster_type.is_nothing


def test_dbt_with_downstream_asset(test_meta_config_manifest: Dict[str, Any]):
    @dbt_assets(manifest=test_meta_config_manifest)
    def my_dbt_assets(): ...

    @asset(deps=[AssetKey("orders"), AssetKey(["customized", "staging", "payments"])])
    def downstream_of_dbt():
        return None

    assert len(list(downstream_of_dbt.input_names)) == 2
    for input_name in downstream_of_dbt.input_names:
        input_dagster_type = downstream_of_dbt.op.ins[input_name].dagster_type

        assert isinstance(input_dagster_type, DagsterType) and input_dagster_type.is_nothing


def test_dbt_with_custom_resource_key(test_meta_config_manifest: Dict[str, Any]) -> None:
    dbt_resource_key = "my_custom_dbt_resource_key"

    @dbt_assets(manifest=test_meta_config_manifest, required_resource_keys={dbt_resource_key})
    def my_dbt_assets(context: AssetExecutionContext):
        dbt = getattr(context.resources, dbt_resource_key)

        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={dbt_resource_key: DbtCliResource(project_dir=os.fspath(test_meta_config_path))},
    )
    assert result.success


def test_dbt_with_dotted_dependency_names(test_dbt_alias_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_alias_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_alias_path))},
    )
    assert result.success


def test_dbt_with_model_versions(test_dbt_model_versions_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_model_versions_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    assert {
        AssetKey(["stg_customers_v1"]),
        AssetKey(["stg_customers_v2"]),
    }.issubset(my_dbt_assets.keys)

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_model_versions_path))},
    )
    assert result.success


def test_dbt_with_python_interleaving(
    test_dbt_python_interleaving_manifest: Dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_dbt_python_interleaving_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    assert set(my_dbt_assets.keys_by_input_name.values()) == {
        AssetKey(["dagster", "python_augmented_customers"]),
        # these inputs are necessary for copies of this asset to properly reflect the dependencies
        # of this asset when it is automatically subset
        AssetKey("raw_customers"),
        AssetKey("raw_orders"),
        AssetKey("raw_payments"),
        AssetKey("stg_orders"),
        AssetKey("stg_payments"),
    }

    @asset(key_prefix="dagster", deps=["raw_customers"])
    def python_augmented_customers(): ...

    defs = Definitions(
        assets=[my_dbt_assets, python_augmented_customers],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_python_interleaving_path))},
    )
    global_job = defs.get_implicit_global_asset_job_def()
    # my_dbt_assets gets split up
    assert global_job.dependencies == {
        # no dependencies for the first invocation of my_dbt_assets
        NodeInvocation(name="my_dbt_assets", alias="my_dbt_assets_2"): {},
        # the python augmented customers asset depends on the second invocation of my_dbt_assets
        NodeInvocation(name="dagster__python_augmented_customers"): {
            "raw_customers": DependencyDefinition(
                node="my_dbt_assets_2", output="seed_jaffle_shop_raw_customers"
            )
        },
        # the second invocation of my_dbt_assets depends on the first, and the python step
        NodeInvocation(name="my_dbt_assets"): {
            "__subset_input__model_jaffle_shop_stg_orders": DependencyDefinition(
                node="my_dbt_assets_2", output="model_jaffle_shop_stg_orders"
            ),
            "__subset_input__model_jaffle_shop_stg_payments": DependencyDefinition(
                node="my_dbt_assets_2", output="model_jaffle_shop_stg_payments"
            ),
            "dagster_python_augmented_customers": DependencyDefinition(
                node="dagster__python_augmented_customers", output="result"
            ),
        },
    }
    # two distinct node definitions, but 3 nodes overall
    assert len(global_job.all_node_defs) == 2
    assert len(global_job.nodes) == 3

    result = global_job.execute_in_process()
    assert result.success

    # now make sure that if you just select these two, we still get a valid dependency graph (where)
    # customers executes after its parent "stg_orders", even though the python step is not selected
    subset_job = global_job.get_subset(
        asset_selection={AssetKey("stg_orders"), AssetKey("customers")}
    )
    assert subset_job.dependencies == {
        # no dependencies for the first invocation of my_dbt_assets
        NodeInvocation(name="my_dbt_assets", alias="my_dbt_assets_2"): {},
        # the second invocation of my_dbt_assets depends on the first
        NodeInvocation(name="my_dbt_assets"): {
            "__subset_input__model_jaffle_shop_stg_orders": DependencyDefinition(
                node="my_dbt_assets_2", output="model_jaffle_shop_stg_orders"
            )
        },
    }
    result = subset_job.execute_in_process()
    assert result.success


def test_dbt_with_semantic_models(test_dbt_semantic_models_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_semantic_models_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_semantic_models_path))},
    )
    assert result.success


@pytest.mark.skipif(
    version.parse(dbt_version) < version.parse("1.8.0"),
    reason="dbt unit test support is only available in `dbt-core>=1.8.0`",
)
@pytest.mark.parametrize("select", ["fqn:*", "tag:test"])
def test_dbt_with_unit_tests(test_dbt_unit_tests_manifest: Dict[str, Any], select: str) -> None:
    @dbt_assets(
        manifest=test_dbt_unit_tests_manifest,
        select=select,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_unit_tests_path))},
    )
    assert result.success


def test_dbt_with_invalid_self_dependencies(
    test_asset_key_exceptions_manifest: Dict[str, Any],
) -> None:
    expected_error_message = "\n".join(
        [
            "The following dbt resources have the asset key `['jaffle_shop', 'stg_customers']`:",
            "  - `model.test_dagster_asset_key_exceptions.stg_customers` (models/staging/stg_customers.sql)",
            "  - `source.test_dagster_asset_key_exceptions.jaffle_shop.stg_customers` (models/sources.yml)",
        ]
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=DUPLICATE_ASSET_KEY_ERROR_MESSAGE,
    ) as exc_info:

        @dbt_assets(manifest=test_asset_key_exceptions_manifest)
        def my_dbt_assets(): ...

    assert expected_error_message in str(exc_info.value)


def test_dbt_with_duplicate_asset_keys(test_meta_config_manifest: Dict[str, Any]) -> None:
    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            asset_key = super().get_asset_key(dbt_resource_props)
            if asset_key in [AssetKey("orders"), AssetKey("customers")]:
                return AssetKey(["duplicate"])

            return asset_key

    expected_error_message = "\n".join(
        [
            "The following dbt resources have the asset key `['duplicate']`:",
            "  - `model.test_dagster_meta_config.customers` (models/customers.sql)",
            "  - `model.test_dagster_meta_config.orders` (models/orders.sql)",
        ]
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=DUPLICATE_ASSET_KEY_ERROR_MESSAGE,
    ) as exc_info:

        @dbt_assets(
            manifest=test_meta_config_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
        def my_dbt_assets(): ...

    assert expected_error_message in str(exc_info.value)


def test_dbt_with_duplicate_source_asset_keys(
    test_duplicate_source_asset_key_manifest: Dict[str, Any],
) -> None:
    expected_error_message = "\n".join(
        [
            "The following dbt resources have the asset key `['duplicate']`:",
            "  - `source.test_dagster_duplicate_source_asset_key.jaffle_shop.raw_customers` (models/sources.yml)",
            "  - `source.test_dagster_duplicate_source_asset_key.jaffle_shop.raw_orders` (models/sources.yml)",
            "  - `source.test_dagster_duplicate_source_asset_key.jaffle_shop.raw_payments` (models/sources.yml)",
        ]
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=DUPLICATE_ASSET_KEY_ERROR_MESSAGE,
    ) as exc_info:

        @dbt_assets(manifest=test_duplicate_source_asset_key_manifest)
        def my_dbt_assets_with_duplicate_source_asset_keys(): ...

    assert expected_error_message in str(exc_info.value)

    # Duplicate dbt model asset keys are still not allowed.
    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            asset_key = super().get_asset_key(dbt_resource_props)
            if asset_key in [AssetKey("orders"), AssetKey("customers")]:
                return AssetKey(["duplicate"])

            return asset_key

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=DUPLICATE_ASSET_KEY_ERROR_MESSAGE,
    ):

        @dbt_assets(
            manifest=test_duplicate_source_asset_key_manifest,
            dagster_dbt_translator=CustomDagsterDbtTranslator(
                settings=DagsterDbtTranslatorSettings(enable_duplicate_source_asset_keys=True)
            ),
        )
        def my_dbt_assets_with_duplicate_model_asset_keys(): ...

    @dbt_assets(
        manifest=test_duplicate_source_asset_key_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_duplicate_source_asset_keys=True)
        ),
    )
    def my_dbt_assets(): ...

    assert set(my_dbt_assets.keys_by_input_name.values()) == {
        AssetKey(["duplicate"]),
        AssetKey(["stg_customers"]),
        AssetKey(["stg_orders"]),
        AssetKey(["stg_payments"]),
    }
    assert set(my_dbt_assets.keys_by_output_name.values()) == {
        AssetKey(["stg_customers"]),
        AssetKey(["stg_orders"]),
        AssetKey(["stg_payments"]),
        AssetKey(["customers"]),
        AssetKey(["orders"]),
    }

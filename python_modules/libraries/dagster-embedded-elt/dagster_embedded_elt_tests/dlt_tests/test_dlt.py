import os
from typing import Optional

import dlt
import duckdb
import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AutoMaterializePolicy,
    AutoMaterializeRule,
    Definitions,
)
from dagster._core.definitions.auto_materialize_rule import MaterializeOnCronRule
from dagster._core.definitions.materialize import materialize
from dagster_embedded_elt.dlt.asset_decorator import dlt_assets
from dagster_embedded_elt.dlt.resource import DagsterDltResource
from dagster_embedded_elt.dlt.translator import DagsterDltTranslator
from dlt.extract.resource import DltResource

from .dlt_test_sources.duckdb_with_transformer import pipeline

EXAMPLE_PIPELINE_DUCKDB = "example_pipeline.duckdb"

DLT_SOURCE = pipeline()
DLT_PIPELINE = dlt.pipeline(
    pipeline_name="example_pipeline",
    dataset_name="example",
    destination="duckdb",
)


@pytest.fixture
def _teardown():
    yield
    if os.path.exists(EXAMPLE_PIPELINE_DUCKDB):
        os.remove(EXAMPLE_PIPELINE_DUCKDB)


def test_example_pipeline_asset_keys():
    @dlt_assets(dlt_source=DLT_SOURCE, dlt_pipeline=DLT_PIPELINE)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    assert {
        AssetKey("dlt_pipeline_repos"),
        AssetKey("dlt_pipeline_repo_issues"),
    } == example_pipeline_assets.keys


def test_example_pipeline(_teardown):
    @dlt_assets(dlt_source=DLT_SOURCE, dlt_pipeline=DLT_PIPELINE)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success

    with duckdb.connect(database=EXAMPLE_PIPELINE_DUCKDB, read_only=True) as conn:
        row = conn.execute("select count(*) from example.repos").fetchone()
        assert row and row[0] == 3

        row = conn.execute("select count(*) from example.repo_issues").fetchone()
        assert row and row[0] == 7


def test_multi_asset_names_do_not_conflict(_teardown):
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_asset_key(self, resource: DltResource) -> AssetKey:
            return AssetKey("custom_" + resource.name)

    @dlt_assets(dlt_source=DLT_SOURCE, dlt_pipeline=DLT_PIPELINE, name="multi_asset_name1")
    def assets1():
        pass

    @dlt_assets(
        dlt_source=DLT_SOURCE,
        dlt_pipeline=DLT_PIPELINE,
        name="multi_asset_name2",
        dlt_dagster_translator=CustomDagsterDltTranslator(),
    )
    def assets2():
        pass

    assert Definitions(assets=[assets1, assets2])


def test_get_materialize_policy(_teardown):
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_auto_materialize_policy(
            self, resource: DltResource
        ) -> Optional[AutoMaterializePolicy]:
            return AutoMaterializePolicy.eager().with_rules(
                AutoMaterializeRule.materialize_on_cron("0 1 * * *")
            )

    @dlt_assets(
        dlt_source=DLT_SOURCE,
        dlt_pipeline=DLT_PIPELINE,
        dlt_dagster_translator=CustomDagsterDltTranslator(),
    )
    def assets():
        pass

    for item in assets.auto_materialize_policies_by_key.values():
        assert any(
            isinstance(rule, MaterializeOnCronRule) and rule.cron_schedule == "0 1 * * *"
            for rule in item.rules
        )


def test_example_pipeline_has_required_metadata_keys(_teardown):
    required_metadata_keys = {
        "destination_type",
        "destination_name",
        "dataset_name",
        "first_run",
        "started_at",
        "finished_at",
        "jobs",
    }

    @dlt_assets(dlt_source=DLT_SOURCE, dlt_pipeline=DLT_PIPELINE)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        for asset in dlt_pipeline_resource.run(context=context):
            assert asset.metadata
            assert all(key in asset.metadata.keys() for key in required_metadata_keys)
            yield asset

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success


def test_example_pipeline_subselection(_teardown):
    @dlt_assets(dlt_source=DLT_SOURCE, dlt_pipeline=DLT_PIPELINE)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
        selection=[AssetKey(["dlt_pipeline_repos"])],
    )
    assert res.success
    materialization_events = res.get_asset_materialization_events()
    assert len(materialization_events) == 1

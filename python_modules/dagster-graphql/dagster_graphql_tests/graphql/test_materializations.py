from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector
from dagster_graphql_tests.graphql.setup import LONG_INT

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .utils import sync_execute_get_events

ASSET_TAGS_QUERY = """
    query AssetQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                tags {
                    key
                    value
                }
            }
        }
    }
"""


class TestMaterializations(ExecutingGraphQLContextTestMatrix):
    def test_materializations(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "materialization_pipeline")
        logs = sync_execute_get_events(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                }
            },
        )

        materializations = [log for log in logs if log["__typename"] == "StepMaterializationEvent"]
        assert len(materializations) == 1
        mat = materializations[0]["materialization"]
        assert mat["label"] == "all_types"

        text_entry = mat["metadataEntries"][0]
        assert text_entry["__typename"] == "EventTextMetadataEntry"
        assert text_entry["text"]

        text_entry = mat["metadataEntries"][1]
        assert text_entry["__typename"] == "EventUrlMetadataEntry"
        assert text_entry["url"]

        text_entry = mat["metadataEntries"][2]
        assert text_entry["__typename"] == "EventPathMetadataEntry"
        assert text_entry["path"]

        text_entry = mat["metadataEntries"][3]
        assert text_entry["__typename"] == "EventJsonMetadataEntry"
        assert text_entry["jsonString"]

        text_entry = mat["metadataEntries"][4]
        assert text_entry["__typename"] == "EventPythonArtifactMetadataEntry"
        assert text_entry["module"]
        assert text_entry["name"]

        text_entry = mat["metadataEntries"][5]
        assert text_entry["__typename"] == "EventPythonArtifactMetadataEntry"
        assert text_entry["module"]
        assert text_entry["name"]

        text_entry = mat["metadataEntries"][6]
        assert text_entry["__typename"] == "EventFloatMetadataEntry"
        assert text_entry["floatValue"]

        text_entry = mat["metadataEntries"][7]
        assert text_entry["__typename"] == "EventIntMetadataEntry"
        assert text_entry["intRepr"]

        text_entry = mat["metadataEntries"][8]
        assert text_entry["__typename"] == "EventFloatMetadataEntry"
        assert text_entry["floatValue"] is None  # float NaN test

        text_entry = mat["metadataEntries"][9]
        assert text_entry["__typename"] == "EventIntMetadataEntry"
        assert int(text_entry["intRepr"]) == LONG_INT

        text_entry = mat["metadataEntries"][10]
        assert text_entry["__typename"] == "EventPipelineRunMetadataEntry"
        assert text_entry["runId"] == "fake_run_id"

        text_entry = mat["metadataEntries"][11]
        assert text_entry["__typename"] == "EventAssetMetadataEntry"
        assert text_entry["assetKey"]
        assert text_entry["assetKey"]["path"]

        non_engine_event_logs = [
            message for message in logs if message["__typename"] != "EngineEvent"
        ]

        snapshot.assert_match([message["__typename"] for message in non_engine_event_logs])

    def test_materialization_backcompat(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "backcompat_materialization_pipeline")
        sync_execute_get_events(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                }
            },
        )
        result = execute_dagster_graphql(
            graphql_context, ASSET_TAGS_QUERY, variables={"assetKey": {"path": ["all_types"]}}
        )
        assert result.data
        assert result.data["assetOrError"]
        assert result.data["assetOrError"]["tags"] is not None
        snapshot.assert_match(result.data)

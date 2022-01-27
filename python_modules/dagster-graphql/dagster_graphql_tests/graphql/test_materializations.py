from dagster_graphql.test.utils import infer_pipeline_selector
from dagster_graphql_tests.graphql.setup import LONG_INT

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .utils import sync_execute_get_events


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

        materializations = [log for log in logs if log["__typename"] == "MaterializationEvent"]
        assert len(materializations) == 1
        mat = materializations[0]
        assert mat["label"] == "all_types"

        entry = mat["metadataEntries"][0]
        assert entry["__typename"] == "EventTextMetadataEntry"
        assert entry["text"]

        entry = mat["metadataEntries"][1]
        assert entry["__typename"] == "EventUrlMetadataEntry"
        assert entry["url"]

        entry = mat["metadataEntries"][2]
        assert entry["__typename"] == "EventPathMetadataEntry"
        assert entry["path"]

        entry = mat["metadataEntries"][3]
        assert entry["__typename"] == "EventJsonMetadataEntry"
        assert entry["jsonString"]

        entry = mat["metadataEntries"][4]
        assert entry["__typename"] == "EventPythonArtifactMetadataEntry"
        assert entry["module"]
        assert entry["name"]

        entry = mat["metadataEntries"][5]
        assert entry["__typename"] == "EventPythonArtifactMetadataEntry"
        assert entry["module"]
        assert entry["name"]

        entry = mat["metadataEntries"][6]
        assert entry["__typename"] == "EventFloatMetadataEntry"
        assert entry["floatValue"]

        entry = mat["metadataEntries"][7]
        assert entry["__typename"] == "EventIntMetadataEntry"
        assert entry["intRepr"]

        entry = mat["metadataEntries"][8]
        assert entry["__typename"] == "EventFloatMetadataEntry"
        assert entry["floatValue"] is None  # float NaN test

        entry = mat["metadataEntries"][9]
        assert entry["__typename"] == "EventIntMetadataEntry"
        assert int(entry["intRepr"]) == LONG_INT

        entry = mat["metadataEntries"][10]
        assert entry["__typename"] == "EventPipelineRunMetadataEntry"
        assert entry["runId"] == "fake_run_id"

        entry = mat["metadataEntries"][11]
        assert entry["__typename"] == "EventAssetMetadataEntry"
        assert entry["assetKey"]
        assert entry["assetKey"]["path"]

        entry = mat["metadataEntries"][12]
        assert entry["__typename"] == "EventTableMetadataEntry"
        assert entry["table"]
        assert entry["table"]["records"]
        assert entry["table"]["schema"]

        entry = mat["metadataEntries"][13]
        assert entry["__typename"] == "EventTableSchemaMetadataEntry"
        assert entry["schema"]
        assert entry["schema"]["columns"]
        assert entry["schema"]["columns"][0]["constraints"]
        assert entry["schema"]["constraints"]

        non_engine_event_logs = [
            message for message in logs if message["__typename"] != "EngineEvent"
        ]

        snapshot.assert_match([message["__typename"] for message in non_engine_event_logs])

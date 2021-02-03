from dagster_graphql.test.utils import infer_pipeline_selector

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
        assert text_entry["intValue"]

        non_engine_event_logs = [
            message for message in logs if message["__typename"] != "EngineEvent"
        ]

        snapshot.assert_match([message["__typename"] for message in non_engine_event_logs])

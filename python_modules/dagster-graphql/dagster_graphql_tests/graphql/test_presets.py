import re
from collections import OrderedDict

from dagster_graphql.test.preset_query import execute_preset_query

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix


class TestPresets(ReadonlyGraphQLContextTestMatrix):
    def test_basic_preset_query_no_presets(self, graphql_context):
        result = execute_preset_query("csv_hello_world_two", graphql_context)
        assert result.data == OrderedDict(
            [("pipelineOrError", OrderedDict([("name", "csv_hello_world_two"), ("presets", [])]))]
        )

    def test_basic_preset_query_with_presets(self, graphql_context, snapshot):
        result = execute_preset_query("csv_hello_world", graphql_context)

        assert [
            preset_data["name"] for preset_data in result.data["pipelineOrError"]["presets"]
        ] == [
            "prod",
            "test",
            "test_inline",
        ]

        # Remove local filepath from snapshot
        result.data["pipelineOrError"]["presets"][2]["runConfigYaml"] = re.sub(
            r"num: .*/data/num.csv",
            "num: /data/num.csv",
            result.data["pipelineOrError"]["presets"][2]["runConfigYaml"],
        )
        snapshot.assert_match(result.data)

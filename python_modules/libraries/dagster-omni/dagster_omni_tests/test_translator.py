from dagster import AssetKey
from dagster_omni.translator import DefaultOmniTranslator, OmniContentType, OmniTranslatorData


class TestDefaultOmniTranslator:
    def test_get_asset_key_model(self, sample_model_data):
        translator = DefaultOmniTranslator()
        key = translator.get_asset_key(OmniContentType.MODEL, sample_model_data)

        assert key == AssetKey(["omni", "model", "Sales Model_model_123"])

    def test_get_asset_key_workbook(self, sample_workbook_data):
        translator = DefaultOmniTranslator()
        key = translator.get_asset_key(OmniContentType.WORKBOOK, sample_workbook_data)

        assert key == AssetKey(["omni", "workbook", "Sales Analysis_workbook_789"])

    def test_get_asset_key_query(self, sample_query_data):
        translator = DefaultOmniTranslator()
        key = translator.get_asset_key(OmniContentType.QUERY, sample_query_data)

        assert key == AssetKey(["omni", "query", "Monthly Sales_query_abc"])

    def test_get_description_model(self, sample_model_data):
        translator = DefaultOmniTranslator()
        description = translator.get_description(OmniContentType.MODEL, sample_model_data)

        assert "Sales Model" in description
        assert "Data model providing structured access" in description

    def test_get_description_workbook(self, sample_workbook_data):
        translator = DefaultOmniTranslator()
        description = translator.get_description(OmniContentType.WORKBOOK, sample_workbook_data)

        assert "Sales Analysis" in description
        assert "Analysis workbook containing queries" in description

    def test_get_description_query(self, sample_query_data):
        translator = DefaultOmniTranslator()
        description = translator.get_description(OmniContentType.QUERY, sample_query_data)

        assert "Monthly Sales" in description
        assert "Executable query that produces" in description

    def test_get_metadata(self, sample_model_data):
        translator = DefaultOmniTranslator()
        metadata = translator.get_metadata(
            OmniContentType.MODEL, sample_model_data, "https://test.omniapp.co"
        )

        assert metadata["dagster_omni/id"] == "model_123"
        assert metadata["dagster_omni/workspace_url"] == "https://test.omniapp.co"
        assert metadata["dagster_omni/content_type"] == "model"
        assert metadata["dagster_omni/name"] == "Sales Model"
        assert metadata["dagster_omni/created_at"] == "2024-01-01T00:00:00Z"

    def test_get_tags(self, sample_model_data):
        translator = DefaultOmniTranslator()
        tags = translator.get_tags(OmniContentType.MODEL, sample_model_data)

        assert tags["dagster_omni/asset_type"] == "model"

    def test_get_deps_workbook(self, sample_workspace_data):
        translator = DefaultOmniTranslator()

        workbook_content = sample_workspace_data.workbooks_by_id["workbook_789"]
        translator_data = OmniTranslatorData(
            content_data=workbook_content,
            workspace_data=sample_workspace_data,
        )

        deps = translator.get_deps(translator_data)

        # Workbook should depend on the model it references
        assert len(deps) == 1
        assert deps[0] == AssetKey(["omni", "model", "Sales Model_model_123"])

    def test_get_deps_query(self, sample_workspace_data):
        translator = DefaultOmniTranslator()

        query_content = sample_workspace_data.queries_by_id["query_abc"]
        translator_data = OmniTranslatorData(
            content_data=query_content,
            workspace_data=sample_workspace_data,
        )

        deps = translator.get_deps(translator_data)

        # Query should depend on the workbook it belongs to
        assert len(deps) == 1
        assert deps[0] == AssetKey(["omni", "workbook", "Sales Analysis_workbook_789"])

    def test_get_model_asset_spec(self, sample_workspace_data):
        translator = DefaultOmniTranslator()

        model_content = sample_workspace_data.models_by_id["model_123"]
        translator_data = OmniTranslatorData(
            content_data=model_content,
            workspace_data=sample_workspace_data,
        )

        spec = translator.get_model_asset_spec(translator_data)

        assert spec.key == AssetKey(["omni", "model", "Sales Model_model_123"])
        assert "Sales Model" in spec.description
        assert spec.metadata["dagster_omni/id"] == "model_123"
        assert spec.tags["dagster_omni/asset_type"] == "model"
        assert len(spec.deps) == 0  # Models have no dependencies in our test data

    def test_get_workbook_asset_spec(self, sample_workspace_data):
        translator = DefaultOmniTranslator()

        workbook_content = sample_workspace_data.workbooks_by_id["workbook_789"]
        translator_data = OmniTranslatorData(
            content_data=workbook_content,
            workspace_data=sample_workspace_data,
        )

        spec = translator.get_workbook_asset_spec(translator_data)

        assert spec.key == AssetKey(["omni", "workbook", "Sales Analysis_workbook_789"])
        assert "Sales Analysis" in spec.description
        assert spec.metadata["dagster_omni/id"] == "workbook_789"
        assert spec.tags["dagster_omni/asset_type"] == "workbook"
        assert len(spec.deps) == 1  # Should depend on the model

    def test_get_query_asset_spec(self, sample_workspace_data):
        translator = DefaultOmniTranslator()

        query_content = sample_workspace_data.queries_by_id["query_abc"]
        translator_data = OmniTranslatorData(
            content_data=query_content,
            workspace_data=sample_workspace_data,
        )

        spec = translator.get_query_asset_spec(translator_data)

        assert spec.key == AssetKey(["omni", "query", "Monthly Sales_query_abc"])
        assert "Monthly Sales" in spec.description
        assert spec.metadata["dagster_omni/id"] == "query_abc"
        assert spec.tags["dagster_omni/asset_type"] == "query"
        assert len(spec.deps) == 1  # Should depend on the workbook

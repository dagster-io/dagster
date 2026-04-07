import dagster as dg
from project_datastage.components.data_stage_job_component import (
    DataStageJobComponent,
    DataStageProject,
    DataStageTranslator,
    datastage_assets,
)
from project_datastage.components.scheduled_job_component import ScheduledJobComponent


def test_translator_asset_key():
    translator = DataStageTranslator()
    table_def = {"name": "customers", "source_schema": "LEGACY"}
    key = translator.get_asset_key(table_def)
    assert key == dg.AssetKey(["datastage_raw", "customers"])


def test_translator_group_and_tags():
    translator = DataStageTranslator()
    table_def = {"name": "orders"}
    assert translator.get_group_name(table_def) == "datastage_replication"
    tags = translator.get_tags(table_def)
    assert tags["source_system"] == "ibm_datastage"


def test_datastage_assets_creates_specs():
    project = DataStageProject(
        {
            "job_name": "test_job",
            "source_connection": {},
            "target_connection": {},
            "tables": [
                {"name": "customers"},
                {"name": "orders"},
            ],
        }
    )
    decorator = datastage_assets(project=project, name="test_replication")
    assert callable(decorator)


def test_datastage_job_component_build_defs():
    component = DataStageJobComponent(
        demo_mode=True,
        job_name="test_job",
        tables=[
            {"name": "customers", "source_schema": "LEGACY", "target_schema": "RAW"},
        ],
    )
    result = component.build_defs(context=None)
    assert isinstance(result, dg.Definitions)


def test_scheduled_job_component_importable():
    assert callable(ScheduledJobComponent)

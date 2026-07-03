"""Tests for resource renaming functionality."""

import dagster as dg
import pytest


def test_op_definition_rename_resources():
    """Test OpDefinition.rename_resources renames resource keys correctly."""
    @dg.op(
        required_resource_keys={"database", "api"},
        ins={"data": dg.In(input_manager_key="input_mgr")},
        outs={"result": dg.Out(io_manager_key="output_mgr")}
    )
    def my_op(context, data):
        return data
    
    # Rename resources
    renamed_op = my_op.rename_resources({
        "database": "new_database",
        "input_mgr": "new_input_mgr",
        "output_mgr": "new_output_mgr"
    })
    
    # Check required resource keys
    assert "new_database" in renamed_op.required_resource_keys
    assert "api" in renamed_op.required_resource_keys  # unchanged
    assert "database" not in renamed_op.required_resource_keys
    
    # Check input manager key
    assert renamed_op.input_def_named("data").input_manager_key == "new_input_mgr"
    
    # Check output manager key  
    assert renamed_op.output_def_named("result").io_manager_key == "new_output_mgr"
    
    # Original op should be unchanged
    assert "database" in my_op.required_resource_keys
    assert my_op.input_def_named("data").input_manager_key == "input_mgr"


def test_op_definition_rename_resources_validation():
    """Test OpDefinition.rename_resources validates resource mapping."""
    @dg.op(required_resource_keys={"database"})
    def my_op(context):
        pass
    
    # Should raise error for invalid resource mapping
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="not found"):
        my_op.rename_resources({"nonexistent": "new_name"})


def test_job_definition_rename_resources():
    """Test JobDefinition.rename_resources renames resource keys correctly."""
    @dg.resource
    def db_resource():
        return "database"
    
    @dg.resource
    def api_resource():
        return "api"
    
    @dg.op(required_resource_keys={"database"})
    def my_op(context):
        return context.resources.database
    
    @dg.job(resource_defs={"database": db_resource, "api": api_resource})
    def my_job():
        my_op()
    
    # Rename resources
    renamed_job = my_job.rename_resources({
        "database": "new_database", 
        "api": "new_api"
    })
    
    # Check resource_defs keys
    assert "new_database" in renamed_job.resource_defs
    assert "new_api" in renamed_job.resource_defs
    assert "database" not in renamed_job.resource_defs
    assert "api" not in renamed_job.resource_defs
    
    # Check that the resource definitions themselves are the same
    assert renamed_job.resource_defs["new_database"] == db_resource
    assert renamed_job.resource_defs["new_api"] == api_resource
    
    # Original job should be unchanged
    assert "database" in my_job.resource_defs
    assert "api" in my_job.resource_defs


def test_assets_definition_rename_resources():
    """Test AssetsDefinition.rename_resources renames resource keys correctly."""
    @dg.resource
    def db_resource():
        return "database"
    
    @dg.asset(resource_defs={"database": db_resource})
    def my_asset(context):
        return context.resources.database
    
    # Rename resources
    renamed_asset = my_asset.rename_resources({"database": "new_database"})
    
    # Check resource_defs keys
    assert "new_database" in renamed_asset.resource_defs
    assert "database" not in renamed_asset.resource_defs
    
    # Check that the resource definition itself is the same
    assert renamed_asset.resource_defs["new_database"] == db_resource
    
    # Original asset should be unchanged
    assert "database" in my_asset.resource_defs


def test_schedule_definition_rename_resources():
    """Test ScheduleDefinition.rename_resources renames resource keys correctly."""
    @dg.resource
    def db_resource():
        return "database"
    
    @dg.op(required_resource_keys={"database"})
    def my_op(context):
        return context.resources.database
    
    @dg.job(resource_defs={"database": db_resource})
    def my_job():
        my_op()
    
    @dg.schedule(cron_schedule="0 0 * * *", job=my_job)
    def my_schedule():
        return {}
    
    # Rename resources
    renamed_schedule = my_schedule.rename_resources({"database": "new_database"})
    
    # The renamed schedule should have a job with renamed resources
    assert "new_database" in renamed_schedule.job.resource_defs
    assert "database" not in renamed_schedule.job.resource_defs
    
    # Original schedule should be unchanged
    assert "database" in my_schedule.job.resource_defs


def test_rename_resources_empty_mapping():
    """Test that empty resource mapping returns equivalent definition."""
    @dg.op(required_resource_keys={"database"})
    def my_op(context):
        pass
    
    renamed_op = my_op.rename_resources({})
    
    # Should have same resource keys
    assert renamed_op.required_resource_keys == my_op.required_resource_keys


def test_rename_resources_partial_mapping():
    """Test that partial resource mapping only renames specified keys."""
    @dg.op(required_resource_keys={"database", "api", "cache"})  
    def my_op(context):
        pass
    
    renamed_op = my_op.rename_resources({"database": "new_database"})
    
    # Only database should be renamed
    assert "new_database" in renamed_op.required_resource_keys
    assert "api" in renamed_op.required_resource_keys
    assert "cache" in renamed_op.required_resource_keys
    assert "database" not in renamed_op.required_resource_keys


def test_input_output_manager_key_renaming():
    """Test that input and output manager keys are properly renamed."""
    @dg.op(
        ins={"input1": dg.In(input_manager_key="mgr1"), "input2": dg.In(input_manager_key="mgr2")},
        outs={"out1": dg.Out(io_manager_key="mgr3"), "out2": dg.Out(io_manager_key="mgr4")}
    )
    def my_op(context, input1, input2):
        return input1, input2
    
    renamed_op = my_op.rename_resources({
        "mgr1": "new_mgr1",
        "mgr3": "new_mgr3"
    })
    
    # Check renamed keys
    assert renamed_op.input_def_named("input1").input_manager_key == "new_mgr1"
    assert renamed_op.input_def_named("input2").input_manager_key == "mgr2"  # unchanged
    assert renamed_op.output_def_named("out1").io_manager_key == "new_mgr3"
    assert renamed_op.output_def_named("out2").io_manager_key == "mgr4"  # unchanged
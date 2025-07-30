import pytest


def test_databricks_session_component_error():
    """Test that DatabricksSessionComponent raises an error if dagster-databricks[connect] is not installed."""
    with pytest.raises(ImportError, match="databricks-connect is not installed"):
        from dagster_databricks import DatabricksSessionComponent as DatabricksSessionComponent

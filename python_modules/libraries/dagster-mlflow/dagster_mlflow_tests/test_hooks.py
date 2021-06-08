from unittest.mock import Mock

from dagster_mlflow.hooks import _cleanup_on_success


def test_cleanup_on_success():

    # Given: - two mock solids
    mock_solid_1 = Mock(name="solid_1")
    mock_solid_2 = Mock(name="solid_2")

    # - a mock context containing a list of these two solids and a current solid
    mock_context = Mock()
    step_execution_context = (
        mock_context._step_execution_context  # pylint: disable=protected-access
    )
    step_execution_context.pipeline_def.solids_in_topological_order = [
        mock_solid_1,
        mock_solid_2,
    ]
    mock_context.solid = mock_solid_2

    # When: the cleanup function is called with the mock context
    _cleanup_on_success(mock_context)

    # Then:
    # - mlflow.end_run is called if solid is the last solid
    mock_context.resources.mlflow.end_run.assert_called_once()

    # - mlflow.end_run is not called when the solid in the context is not the last solid
    mock_context.reset_mock()
    mock_context.solid = mock_solid_1
    _cleanup_on_success(mock_context)
    mock_context.resources.mlflow.end_run.assert_not_called()

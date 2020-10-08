from docs_snippets.legacy.how_tos import solids

from dagster import Int, String, execute_pipeline, pipeline, solid


@solid
def emit_int(_) -> Int:
    return 5


@solid
def emit_str(_) -> String:
    return "Hello"


def test_solids():
    @pipeline
    def my_pipeline():
        solids.my_solid()
        solids.my_logging_solid()
        solids.my_input_example_solid(emit_str(), emit_int())
        solids.my_input_output_example_solid(emit_int(), emit_int())
        solids.my_explicit_def_solid(emit_int(), emit_int())
        solids.my_typehint_output_solid(emit_int(), emit_int())
        solids.my_yield_solid()
        solids.return_solid()
        solids.yield_solid()
        solids.multiple_output_solid()
        solids.x_solid(None)

    pipeline_result = execute_pipeline(my_pipeline)
    assert pipeline_result.success

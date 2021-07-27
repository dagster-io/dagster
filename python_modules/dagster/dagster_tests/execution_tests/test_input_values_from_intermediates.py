from dagster import InputDefinition, List, Optional, execute_pipeline, lambda_solid, pipeline


def test_from_intermediates_from_multiple_outputs():
    @lambda_solid
    def x():
        return "x"

    @lambda_solid
    def y():
        return "y"

    @lambda_solid(input_defs=[InputDefinition("stuff", Optional[List[str]])])
    def gather(stuff):
        return "{} and {}".format(*stuff)

    @pipeline
    def pipe():
        gather([x(), y()])

    result = execute_pipeline(pipe)

    assert result
    assert result.success
    assert (
        result.result_for_solid("gather")
        .compute_input_event_dict["stuff"]
        .event_specific_data[1]
        .label
        == "stuff"
    )
    assert result.result_for_solid("gather").output_value() == "x and y"


def test_from_intermediates_from_config():
    run_config = {"solids": {"x": {"inputs": {"string_input": {"value": "Dagster is great!"}}}}}

    @lambda_solid
    def x(string_input):
        return string_input

    @pipeline
    def pipe():
        x()

    result = execute_pipeline(pipe, run_config=run_config)

    assert result
    assert result.success
    assert (
        result.result_for_solid("x")
        .compute_input_event_dict["string_input"]
        .event_specific_data[1]
        .label
        == "string_input"
    )
    assert result.result_for_solid("x").output_value() == "Dagster is great!"

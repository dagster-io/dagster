from dagster import composite_solid, execute_pipeline, pipeline, solid


@solid
def hello(_context):
    return "hello"


@solid
def echo(_context, x):
    return x


def test_pipeline_autoalias():
    @pipeline
    def autopipe():
        echo(echo(echo(hello())))

    result = execute_pipeline(autopipe)
    assert result.success == True
    assert result.result_for_handle("echo_3").output_value() == "hello"
    assert result.result_for_handle("echo_2").output_value() == "hello"
    assert result.result_for_handle("echo").output_value() == "hello"
    assert result.result_for_handle("hello").output_value() == "hello"


def test_composite_autoalias():
    @composite_solid
    def mega_echo(foo):
        echo(echo(echo(foo)))

    @pipeline
    def autopipe():
        mega_echo(hello())

    result = execute_pipeline(autopipe)
    assert result.success == True
    assert result.result_for_handle("mega_echo.echo_3").output_value() == "hello"
    assert result.result_for_handle("mega_echo.echo_2").output_value() == "hello"
    assert result.result_for_handle("mega_echo.echo").output_value() == "hello"
    assert result.result_for_handle("hello").output_value() == "hello"

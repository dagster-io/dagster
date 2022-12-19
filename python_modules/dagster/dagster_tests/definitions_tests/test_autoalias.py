from dagster import graph, job, op


@op
def hello(_context):
    return "hello"


@op
def echo(_context, x):
    return x


def test_pipeline_autoalias():
    @job
    def autopipe():
        echo(echo(echo(hello())))

    result = autopipe.execute_in_process()
    assert result.success == True
    assert result.output_for_node("echo_3") == "hello"
    assert result.output_for_node("echo_2") == "hello"
    assert result.output_for_node("echo") == "hello"
    assert result.output_for_node("hello") == "hello"


def test_composite_autoalias():
    @graph
    def mega_echo(foo):
        echo(echo(echo(foo)))

    @job
    def autopipe():
        mega_echo(hello())

    result = autopipe.execute_in_process()
    assert result.success == True
    assert result.output_for_node("mega_echo.echo_3") == "hello"
    assert result.output_for_node("mega_echo.echo_2") == "hello"
    assert result.output_for_node("mega_echo.echo") == "hello"
    assert result.output_for_node("hello") == "hello"

import dagster as dg


@dg.op
def hello(_context):
    return "hello"


@dg.op
def echo(_context, x):
    return x


def test_job_autoalias():
    @dg.job
    def autopipe():
        echo(echo(echo(hello())))

    result = autopipe.execute_in_process()
    assert result.success is True
    assert result.output_for_node("echo_3") == "hello"
    assert result.output_for_node("echo_2") == "hello"
    assert result.output_for_node("echo") == "hello"
    assert result.output_for_node("hello") == "hello"


def test_composite_autoalias():
    @dg.graph
    def mega_echo(foo):
        echo(echo(echo(foo)))

    @dg.job
    def autopipe():
        mega_echo(hello())

    result = autopipe.execute_in_process()
    assert result.success is True
    assert result.output_for_node("mega_echo.echo_3") == "hello"
    assert result.output_for_node("mega_echo.echo_2") == "hello"
    assert result.output_for_node("mega_echo.echo") == "hello"
    assert result.output_for_node("hello") == "hello"

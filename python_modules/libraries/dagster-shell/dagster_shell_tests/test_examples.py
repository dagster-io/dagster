from dagster import execute_pipeline


def test_example_shell_command_solid():
    from .example_shell_command_solid import pipe

    res = execute_pipeline(pipe)
    assert res.success
    assert res.result_for_solid("a").output_value() == "hello, world!\n"


def test_example_shell_script_solid():
    from .example_shell_script_solid import pipe

    res = execute_pipeline(pipe)
    assert res.success
    assert res.result_for_solid("a").output_value() == "hello, world!\n"


def test_example_shell_command_op():
    from .example_shell_command_op import my_graph

    res = my_graph.execute_in_process()
    assert res.success


def test_example_shell_script_op():
    from .example_shell_script_op import my_graph

    res = my_graph.execute_in_process()
    assert res.success

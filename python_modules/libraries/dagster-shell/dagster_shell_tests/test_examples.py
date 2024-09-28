def test_example_shell_command_op():
    from dagster_shell_tests.example_shell_command_op import my_graph

    res = my_graph.execute_in_process()
    assert res.success


def test_example_shell_script_op():
    from dagster_shell_tests.example_shell_script_op import my_graph

    res = my_graph.execute_in_process()
    assert res.success

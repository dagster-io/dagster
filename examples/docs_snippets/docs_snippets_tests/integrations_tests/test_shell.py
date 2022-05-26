from docs_snippets.integrations.shell import shell_job


def test_shell_job():
    result = shell_job.execute_in_process(
        run_config={
            "ops": {"shell_op": {"config": {"env": {"MY_ENV_VAR": "hello world!"}}}}
        }
    )

    assert result.output_for_node("shell_op") == "hello world!\n"

from dagster import build_op_context
from docs_snippets.concepts.configuration.configured_op_example import (
    another_configured_example,
    configured_example,
)


def test_new_op(capsys):
    assert configured_example.name == "configured_example"
    configured_example(None)

    captured = capsys.readouterr()
    assert captured.err.count("wheaties") == 6


def test_another_new_op(capsys):
    assert another_configured_example.name == "another_configured_example"

    context = build_op_context(config=6)
    another_configured_example(context)

    captured = capsys.readouterr()
    assert captured.err.count("wheaties") == 6

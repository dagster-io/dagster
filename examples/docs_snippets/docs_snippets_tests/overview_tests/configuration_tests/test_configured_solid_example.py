from docs_snippets.overview.configuration.configured_solid_example import (
    another_configured_example,
    configured_example,
)

from dagster.utils.test import execute_solid


def test_new_solid(capsys):
    assert configured_example.name == "configured_example"
    execute_solid(configured_example)

    captured = capsys.readouterr()
    assert captured.err.count("wheaties") == 6


def test_another_new_solid(capsys):
    assert another_configured_example.name == "another_configured_example"
    execute_solid(
        another_configured_example,
        None,
        None,
        None,
        {"solids": {"another_configured_example": {"config": 6}}},
    )

    captured = capsys.readouterr()
    assert captured.err.count("wheaties") == 6

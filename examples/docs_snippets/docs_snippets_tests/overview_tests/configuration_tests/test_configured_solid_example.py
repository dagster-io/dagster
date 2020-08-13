from docs_snippets.overview.configuration.configured_solid_example import (
    another_new_solid,
    new_solid,
)

from dagster.utils.test import execute_solid


def test_new_solid(capsys):
    execute_solid(new_solid)

    captured = capsys.readouterr()
    assert captured.err.count('wheaties') == 6


def test_another_new_solid(capsys):
    execute_solid(another_new_solid)

    captured = capsys.readouterr()
    assert captured.err.count('wheaties') == 6

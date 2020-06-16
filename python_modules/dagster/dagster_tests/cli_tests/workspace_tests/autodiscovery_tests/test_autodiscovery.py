import pytest

from dagster import DagsterInvariantViolationError, RepositoryDefinition
from dagster.cli.workspace.autodiscovery import (
    loadable_targets_from_python_file,
    loadable_targets_from_python_module,
)
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import repository_def_from_pointer
from dagster.utils import file_relative_path


def test_single_repository():
    single_repo_path = file_relative_path(__file__, 'single_repository.py')
    loadable_targets = loadable_targets_from_python_file(single_repo_path)

    assert len(loadable_targets) == 1
    symbol = loadable_targets[0].attribute
    assert symbol == 'single_repository'

    repo_def = CodePointer.from_python_file(single_repo_path, symbol).load_target()
    isinstance(repo_def, RepositoryDefinition)
    assert repo_def.name == 'single_repository'


def test_double_repository():
    loadable_repos = loadable_targets_from_python_file(
        file_relative_path(__file__, 'double_repository.py'),
    )

    assert set([lr.target_definition.name for lr in loadable_repos]) == {'repo_one', 'repo_two'}


def test_single_pipeline():
    single_pipeline_path = file_relative_path(__file__, 'single_pipeline.py')
    loadable_targets = loadable_targets_from_python_file(single_pipeline_path)

    assert len(loadable_targets) == 1
    symbol = loadable_targets[0].attribute
    assert symbol == 'a_pipeline'

    repo_def = repository_def_from_pointer(
        CodePointer.from_python_file(single_pipeline_path, symbol)
    )

    isinstance(repo_def, RepositoryDefinition)
    assert repo_def.get_pipeline('a_pipeline')


def test_double_pipeline():
    double_pipeline_path = file_relative_path(__file__, 'double_pipeline.py')
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        loadable_targets_from_python_file(double_pipeline_path)

    assert str(exc_info.value) == (
        "No repository and more than one pipeline found in \"double_pipeline\". "
        "If you load a file or module directly it must either have one repository "
        "or one pipeline in scope. Found pipelines defined in variables or decorated "
        "functions: ['pipe_one', 'pipe_two']."
    )


def test_nada():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        loadable_targets_from_python_file(file_relative_path(__file__, 'nada.py'))

    assert str(exc_info.value) == 'No pipelines or repositories found in "nada".'


def test_single_repository_in_module():
    loadable_targets = loadable_targets_from_python_module(
        'dagster.utils.test.toys.single_repository'
    )
    assert len(loadable_targets) == 1
    symbol = loadable_targets[0].attribute
    assert symbol == 'single_repository'

    repo_def = CodePointer.from_module(
        'dagster.utils.test.toys.single_repository', symbol
    ).load_target()
    isinstance(repo_def, RepositoryDefinition)
    assert repo_def.name == 'single_repository'

import imp
import importlib
import pytest
from dagster.utils import script_relative_path

from dagster.core.definitions import LoaderEntrypoint, PipelineDefinition, RepositoryDefinition
from dagster.core.definitions.decorators import lambda_solid
from dagster.core.definitions.handle import _ExecutionTargetMode
from dagster.cli.load_handle import handle_for_pipeline_cli_args, CliUsageError


def test_repository_python_file():
    python_file = script_relative_path('bar_repo.py')
    module = imp.load_source('bar_repo', python_file)

    handle = handle_for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'python_file': python_file, 'fn_name': 'define_bar_repo'}
    )
    assert handle.mode == _ExecutionTargetMode.REPOSITORY
    assert handle.entrypoint == LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo')
    assert handle.data.pipeline_name == 'foo'

    with pytest.raises(CliUsageError):
        handle_for_pipeline_cli_args(
            {
                'module_name': 'kdjfkd',
                'pipeline_name': 'foo',
                'python_file': script_relative_path('bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': None,
            }
        )

    with pytest.raises(CliUsageError):
        handle_for_pipeline_cli_args(
            {
                'module_name': None,
                'pipeline_name': 'foo',
                'python_file': script_relative_path('bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': 'kjdfkdjf',
            }
        )


def test_repository_module():
    module = importlib.import_module('dagster')

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster',
            'pipeline_name': 'foo',
            'python_file': None,
            'fn_name': 'define_bar_repo',
            'repository_yaml': None,
        }
    )
    assert handle.mode == _ExecutionTargetMode.REPOSITORY
    assert handle.entrypoint == LoaderEntrypoint(module, 'dagster', 'define_bar_repo')
    assert handle.data.pipeline_name == 'foo'


def test_pipeline_python_file():
    python_file = script_relative_path('foo_pipeline.py')
    module = imp.load_source('foo_pipeline', python_file)

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': None,
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': python_file,
            'repository_yaml': None,
        }
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE
    assert handle.entrypoint == LoaderEntrypoint(module, 'foo_pipeline', 'define_pipeline')


def test_pipeline_module():
    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster',
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': None,
            'repository_yaml': None,
        }
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE
    assert handle.entrypoint == LoaderEntrypoint(
        importlib.import_module('dagster'), 'dagster', 'define_pipeline'
    )


def test_yaml_file():
    module = importlib.import_module('dagster_examples.intro_tutorial.repos')

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': None,
            'pipeline_name': 'foobar',
            'python_file': None,
            'fn_name': None,
            'repository_yaml': script_relative_path('repository.yml'),
        }
    )
    assert handle.mode == _ExecutionTargetMode.REPOSITORY
    assert handle.entrypoint == LoaderEntrypoint(
        module, 'dagster_examples.intro_tutorial.repos', 'define_repo'
    )
    assert handle.data.pipeline_name == 'foobar'

    with pytest.raises(CliUsageError):
        assert handle_for_pipeline_cli_args({'module_name': 'kdjfdk', 'pipeline_name': 'foobar'})

    with pytest.raises(CliUsageError):
        assert handle_for_pipeline_cli_args({'fn_name': 'kjdfkd', 'pipeline_name': 'foobar'})

    with pytest.raises(CliUsageError):
        assert handle_for_pipeline_cli_args({'pipeline_name': 'foobar', 'python_file': 'kjdfkdj'})


def test_load_from_repository_file():
    pipeline = handle_for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'python_file': __file__, 'fn_name': 'define_bar_repo'}
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_load_from_repository_module():
    pipeline = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'pipeline_name': 'repo_demo_pipeline',
            'fn_name': 'define_repo',
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_load_from_pipeline_file():
    pipeline = handle_for_pipeline_cli_args(
        {'fn_name': 'define_foo_pipeline', 'python_file': __file__}
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_load_from_pipeline_module():
    pipeline = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'define_repo_demo_pipeline',
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_loader_from_default_repository_module_yaml():
    pipeline = handle_for_pipeline_cli_args(
        {
            'pipeline_name': 'repo_demo_pipeline',
            'repository_yaml': script_relative_path('repository_module.yml'),
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_loader_from_default_repository_file_yaml():
    pipeline = handle_for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'repository_yaml': script_relative_path('repository_file.yml')}
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def define_foo_pipeline():
    @lambda_solid
    def do_something():
        return 1

    return PipelineDefinition(name='foo', solids=[do_something])


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline})

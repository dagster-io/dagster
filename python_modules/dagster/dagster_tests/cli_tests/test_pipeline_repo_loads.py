import pytest

from dagster.cli.load_handle import UsageError, recon_pipeline_for_cli_args
from dagster.core.code_pointer import FileCodePointer, ModuleCodePointer
from dagster.core.definitions import PipelineDefinition, RepositoryDefinition
from dagster.core.definitions.decorators import lambda_solid
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    ReconstructablePipelineFromRepo,
)
from dagster.utils import file_relative_path


def test_repository_python_file():
    python_file = file_relative_path(__file__, 'bar_repo.py')

    recon_pipeline = recon_pipeline_for_cli_args(
        {'pipeline_name': 'foo', 'python_file': python_file, 'fn_name': 'define_bar_repo'}
    )
    assert isinstance(recon_pipeline, ReconstructablePipelineFromRepo)
    assert recon_pipeline.repository.pointer == FileCodePointer(python_file, 'define_bar_repo')
    assert recon_pipeline.pipeline_name == 'foo'

    with pytest.raises(UsageError):
        recon_pipeline_for_cli_args(
            {
                'module_name': 'kdjfkd',
                'pipeline_name': 'foo',
                'python_file': file_relative_path(__file__, 'bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': None,
            }
        )

    with pytest.raises(UsageError):
        recon_pipeline_for_cli_args(
            {
                'module_name': None,
                'pipeline_name': 'foo',
                'python_file': file_relative_path(__file__, 'bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': 'kjdfkdjf',
            }
        )


def test_repository_module():
    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'module_name': 'dagster',
            'pipeline_name': 'foo',
            'python_file': None,
            'fn_name': 'define_bar_repo',
            'repository_yaml': None,
        }
    )
    assert isinstance(recon_pipeline, ReconstructablePipelineFromRepo)
    assert recon_pipeline.repository.pointer == ModuleCodePointer('dagster', 'define_bar_repo')
    assert recon_pipeline.pipeline_name == 'foo'


def test_pipeline_python_file():
    python_file = file_relative_path(__file__, 'foo_pipeline.py')

    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'module_name': None,
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': python_file,
            'repository_yaml': None,
        }
    )
    assert isinstance(recon_pipeline, ReconstructablePipeline)
    assert recon_pipeline.pointer == FileCodePointer(python_file, 'define_pipeline')


def test_pipeline_module():
    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'module_name': 'dagster',
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': None,
            'repository_yaml': None,
        }
    )
    assert isinstance(recon_pipeline, ReconstructablePipeline)
    assert recon_pipeline.pointer == ModuleCodePointer('dagster', 'define_pipeline')


def test_yaml_file():
    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'module_name': None,
            'pipeline_name': 'foobar',
            'python_file': None,
            'fn_name': None,
            'repository_yaml': file_relative_path(__file__, 'repository_module.yaml'),
        }
    )
    assert isinstance(recon_pipeline, ReconstructablePipelineFromRepo)

    assert recon_pipeline.repository.pointer == ModuleCodePointer(
        'dagster_examples.intro_tutorial.repos', 'define_repo'
    )

    with pytest.raises(UsageError):
        assert recon_pipeline_for_cli_args({'module_name': 'kdjfdk', 'pipeline_name': 'foobar'})

    with pytest.raises(UsageError):
        assert recon_pipeline_for_cli_args({'fn_name': 'kjdfkd', 'pipeline_name': 'foobar'})

    with pytest.raises(UsageError):
        assert recon_pipeline_for_cli_args({'pipeline_name': 'foobar', 'python_file': 'kjdfkdj'})


def test_load_from_repository_file():
    recon_pipeline = recon_pipeline_for_cli_args(
        {'pipeline_name': 'foo', 'python_file': __file__, 'fn_name': 'define_bar_repo'}
    )
    pipeline_def = recon_pipeline.get_definition()

    assert isinstance(pipeline_def, PipelineDefinition)
    assert pipeline_def.name == 'foo'


def test_load_from_repository_module():
    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'pipeline_name': 'hello_cereal_pipeline',
            'fn_name': 'define_repo',
        }
    )
    pipeline_def = recon_pipeline.get_definition()

    assert isinstance(pipeline_def, PipelineDefinition)
    assert pipeline_def.name == 'hello_cereal_pipeline'


def test_load_from_pipeline_file():
    recon_pipeline = recon_pipeline_for_cli_args(
        {'fn_name': 'define_foo_pipeline', 'python_file': __file__}
    )
    pipeline_def = recon_pipeline.get_definition()

    assert isinstance(pipeline_def, PipelineDefinition)
    assert pipeline_def.name == 'foo'


def test_load_from_pipeline_module():
    recon_pipeline = recon_pipeline_for_cli_args(
        {'module_name': 'dagster_examples.intro_tutorial.repos', 'fn_name': 'hello_cereal_pipeline'}
    )
    pipeline_def = recon_pipeline.get_definition()

    assert isinstance(pipeline_def, PipelineDefinition)
    assert pipeline_def.name == 'hello_cereal_pipeline'


def test_loader_from_default_repository_module_yaml():
    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'pipeline_name': 'hello_cereal_pipeline',
            'repository_yaml': file_relative_path(__file__, 'repository_module.yaml'),
        }
    )
    pipeline_def = recon_pipeline.get_definition()

    assert isinstance(pipeline_def, PipelineDefinition)
    assert pipeline_def.name == 'hello_cereal_pipeline'


def test_loader_from_default_repository_file_yaml():
    recon_pipeline = recon_pipeline_for_cli_args(
        {
            'pipeline_name': 'foo',
            'repository_yaml': file_relative_path(__file__, 'repository_file.yaml'),
        }
    )
    pipeline_def = recon_pipeline.get_definition()

    assert isinstance(pipeline_def, PipelineDefinition)
    assert pipeline_def.name == 'foo'


def define_foo_pipeline():
    @lambda_solid
    def do_something():
        return 1

    return PipelineDefinition(name='foo', solid_defs=[do_something])


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline})

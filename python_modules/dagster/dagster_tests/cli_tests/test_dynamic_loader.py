import pytest
import imp
import importlib

from dagster import PipelineDefinition, RepositoryDefinition, lambda_solid

from dagster.cli.dynamic_loader import (
    InvalidPipelineLoadingComboError,
    PipelineLoadingModeData,
    PipelineTargetInfo,
    PipelineTargetMode,
    RepositoryTargetInfo,
    LoaderEntrypoint,
    RepositoryData,
    entrypoint_from_repo_target_info,
    create_pipeline_loading_mode_data,
    load_pipeline_from_target_info,
    load_repository_from_target_info,
)

from dagster.utils import script_relative_path


def test_repository_python_file():
    python_file = script_relative_path('bar_repo.py')
    module = imp.load_source('bar_repo', python_file)

    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foo',
            python_file=python_file,
            fn_name='define_bar_repo',
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.REPOSITORY,
        data=RepositoryData(
            entrypoint=LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo', {}),
            pipeline_name='foo',
        ),
    )

    with pytest.raises(InvalidPipelineLoadingComboError):
        create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name='kdjfkd',
                pipeline_name='foo',
                python_file=script_relative_path('bar_repo.py'),
                fn_name='define_bar_repo',
                repository_yaml=None,
            )
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name=None,
                pipeline_name='foo',
                python_file=script_relative_path('bar_repo.py'),
                fn_name='define_bar_repo',
                repository_yaml='kjdfkdjf',
            )
        )


def test_repository_module():
    module = importlib.import_module('dagster')
    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name='dagster',
            pipeline_name='foo',
            python_file=None,
            fn_name='define_bar_repo',
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.REPOSITORY,
        data=RepositoryData(
            entrypoint=LoaderEntrypoint(module, 'dagster', 'define_bar_repo', {}),
            pipeline_name='foo',
        ),
    )


def test_pipeline_python_file():
    python_file = script_relative_path('foo_pipeline.py')
    module = imp.load_source('foo_pipeline', python_file)

    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name=None,
            fn_name='define_pipeline',
            pipeline_name=None,
            python_file=python_file,
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.PIPELINE,
        data=LoaderEntrypoint(module, 'foo_pipeline', 'define_pipeline', {}),
    )


def test_pipeline_module():
    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name='dagster',
            fn_name='define_pipeline',
            pipeline_name=None,
            python_file=None,
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.PIPELINE,
        data=LoaderEntrypoint(importlib.import_module('dagster'), 'dagster', 'define_pipeline', {}),
    )


def test_yaml_file():
    module = importlib.import_module('dagster.tutorials.intro_tutorial.repos')

    assert create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foobar',
            python_file=None,
            fn_name=None,
            repository_yaml=script_relative_path('repository.yml'),
        )
    ) == PipelineLoadingModeData(
        mode=PipelineTargetMode.REPOSITORY,
        data=RepositoryData(
            entrypoint=LoaderEntrypoint(
                module, 'dagster.tutorials.intro_tutorial.repos', 'define_repo', {}
            ),
            pipeline_name='foobar',
        ),
    )

    with pytest.raises(InvalidPipelineLoadingComboError):
        assert create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name='kdjfdk',
                pipeline_name='foobar',
                python_file=None,
                fn_name=None,
                repository_yaml=None,
            )
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        assert create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name=None,
                fn_name='kjdfkd',
                pipeline_name='foobar',
                python_file=None,
                repository_yaml=None,
            )
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        assert create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name=None,
                pipeline_name='foobar',
                python_file='kjdfkdj',
                fn_name=None,
                repository_yaml=None,
            )
        )


def test_load_from_repository_file():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foo',
            python_file=script_relative_path('test_dynamic_loader.py'),
            fn_name='define_bar_repo',
            repository_yaml=None,
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_load_from_repository_module():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name='dagster.tutorials.intro_tutorial.repos',
            pipeline_name='repo_demo_pipeline',
            python_file=None,
            fn_name='define_repo',
            repository_yaml=None,
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_load_from_pipeline_file():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name=None,
            fn_name='define_foo_pipeline',
            pipeline_name=None,
            python_file=script_relative_path('test_dynamic_loader.py'),
            repository_yaml=None,
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_load_from_pipeline_module():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name='dagster.tutorials.intro_tutorial.repos',
            fn_name='define_repo_demo_pipeline',
            pipeline_name=None,
            python_file=None,
            repository_yaml=None,
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_loader_from_default_repository_module_yaml():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='repo_demo_pipeline',
            python_file=None,
            fn_name=None,
            repository_yaml=script_relative_path('repository_module.yml'),
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_loader_from_default_repository_file_yaml():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foo',
            python_file=None,
            fn_name=None,
            repository_yaml=script_relative_path('repository_file.yml'),
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_repo_entrypoints():
    module = importlib.import_module('dagster.tutorials.intro_tutorial.repos')
    assert entrypoint_from_repo_target_info(
        RepositoryTargetInfo(
            repository_yaml=script_relative_path('repository.yml'),
            module_name=None,
            python_file=None,
            fn_name=None,
        )
    ) == LoaderEntrypoint(module, 'dagster.tutorials.intro_tutorial.repos', 'define_repo', {})

    module = importlib.import_module('dagster')
    assert entrypoint_from_repo_target_info(
        RepositoryTargetInfo(
            repository_yaml=None, module_name='dagster', python_file=None, fn_name='define_bar_repo'
        )
    ) == LoaderEntrypoint(module, 'dagster', 'define_bar_repo', {})

    python_file = script_relative_path('bar_repo.py')
    module = imp.load_source('bar_repo', python_file)
    assert entrypoint_from_repo_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name=None,
            python_file=python_file,
            fn_name='define_bar_repo',
        )
    ) == LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo', {})


def test_repo_yaml_module_dynamic_load():
    repository = load_repository_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=script_relative_path('repository_module.yml'),
            module_name=None,
            python_file=None,
            fn_name=None,
        )
    )

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'demo_repository'


def test_repo_yaml_file_dynamic_load():
    repository = load_repository_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=script_relative_path('repository_file.yml'),
            module_name=None,
            python_file=None,
            fn_name=None,
        )
    )

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load():
    repository = load_repository_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name='dagster.tutorials.intro_tutorial.repos',
            python_file=None,
            fn_name='define_repo_demo_pipeline',
        )
    )

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'


def test_repo_file_dynamic_load():
    repository = load_repository_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name=None,
            python_file=script_relative_path('test_dynamic_loader.py'),
            fn_name='define_bar_repo',
        )
    )

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load_from_pipeline():
    repository = load_repository_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name='dagster.tutorials.intro_tutorial.repos',
            python_file=None,
            fn_name='define_repo_demo_pipeline',
        )
    )

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'
    assert repository.get_pipeline('repo_demo_pipeline').name == 'repo_demo_pipeline'


def test_repo_file_dynamic_load_from_pipeline():
    repository = load_repository_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name=None,
            python_file=script_relative_path('test_dynamic_loader.py'),
            fn_name='define_foo_pipeline',
        )
    )

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'
    assert repository.get_pipeline('foo').name == 'foo'


@lambda_solid
def do_something():
    return 1


def define_foo_pipeline():
    return PipelineDefinition(name='foo', solids=[do_something])


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline})

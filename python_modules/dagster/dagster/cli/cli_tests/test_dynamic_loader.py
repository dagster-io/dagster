import pytest

from dagster import (
    PipelineDefinition,
    RepositoryDefinition,
    lambda_solid,
)

from dagster.cli.dynamic_loader import (
    FileTargetFunction,
    InvalidPipelineLoadingComboError,
    PipelineLoadingModeData,
    ModuleTargetFunction,
    PipelineTargetInfo,
    PipelineTargetMode,
    RepositoryModuleData,
    RepositoryPythonFileData,
    RepositoryLoadingModeData,
    RepositoryTargetInfo,
    RepositoryTargetMode,
    RepositoryYamlData,
    create_repository_loading_mode_data,
    create_pipeline_loading_mode_data,
    load_pipeline_from_target_info,
    load_repository_object_from_target_info,
)

from dagster.utils import script_relative_path


def test_repository_python_file():
    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foo',
            python_file='bar_repo.py',
            fn_name='define_bar_repo',
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.REPOSITORY_PYTHON_FILE,
        data=RepositoryPythonFileData(
            file_target_function=FileTargetFunction(
                python_file='bar_repo.py',
                fn_name='define_bar_repo',
            ),
            pipeline_name='foo',
        )
    )

    with pytest.raises(InvalidPipelineLoadingComboError):
        create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name='kdjfkd',
                pipeline_name='foo',
                python_file='bar_repo.py',
                fn_name='define_bar_repo',
                repository_yaml=None,
            )
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        create_pipeline_loading_mode_data(
            PipelineTargetInfo(
                module_name=None,
                pipeline_name='foo',
                python_file='bar_repo.py',
                fn_name='define_bar_repo',
                repository_yaml='kjdfkdjf',
            )
        )


def test_repository_module():
    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name='bar_module',
            pipeline_name='foo',
            python_file=None,
            fn_name='define_bar_repo',
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.REPOSITORY_MODULE,
        data=RepositoryModuleData(
            module_target_function=ModuleTargetFunction(
                module_name='bar_module',
                fn_name='define_bar_repo',
            ),
            pipeline_name='foo',
        )
    )


def test_pipeline_python_file():
    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name=None,
            fn_name='define_pipeline',
            pipeline_name=None,
            python_file='foo.py',
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.PIPELINE_PYTHON_FILE,
        data=FileTargetFunction(
            python_file='foo.py',
            fn_name='define_pipeline',
        ),
    )


def test_pipeline_module():
    mode_data = create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name='foo_module',
            fn_name='define_pipeline',
            pipeline_name=None,
            python_file=None,
            repository_yaml=None,
        )
    )

    assert mode_data == PipelineLoadingModeData(
        mode=PipelineTargetMode.PIPELINE_MODULE,
        data=ModuleTargetFunction(
            module_name='foo_module',
            fn_name='define_pipeline',
        ),
    )


def test_yaml_file():
    assert create_pipeline_loading_mode_data(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foobar',
            python_file=None,
            fn_name=None,
            repository_yaml='some_file.yml',
        )
    ) == PipelineLoadingModeData(
        mode=PipelineTargetMode.REPOSITORY_YAML_FILE,
        data=RepositoryYamlData(repository_yaml='some_file.yml', pipeline_name='foobar')
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
            module_name='dagster.cli.cli_tests.test_dynamic_loader',
            pipeline_name='foo',
            python_file=None,
            fn_name='define_bar_repo',
            repository_yaml=None,
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


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
            module_name='dagster.cli.cli_tests.test_dynamic_loader',
            fn_name='define_foo_pipeline',
            pipeline_name=None,
            python_file=None,
            repository_yaml=None,
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_loader_from_default_repository_module_yaml():
    pipeline = load_pipeline_from_target_info(
        PipelineTargetInfo(
            module_name=None,
            pipeline_name='foo',
            python_file=None,
            fn_name=None,
            repository_yaml=script_relative_path('repository_module.yml'),
        )
    )

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


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


def test_repo_mode_data():
    assert create_repository_loading_mode_data(
        RepositoryTargetInfo(
            repository_yaml='foo.yaml',
            module_name=None,
            python_file=None,
            fn_name=None,
        )
    ) == RepositoryLoadingModeData(
        mode=RepositoryTargetMode.YAML_FILE,
        data='foo.yaml',
    )

    assert create_repository_loading_mode_data(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name='foo',
            python_file=None,
            fn_name='define_bar_repo',
        )
    ) == RepositoryLoadingModeData(
        mode=RepositoryTargetMode.MODULE,
        data=ModuleTargetFunction(
            module_name='foo',
            fn_name='define_bar_repo',
        )
    )

    assert create_repository_loading_mode_data(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name=None,
            python_file='foo.py',
            fn_name='define_bar_repo',
        )
    ) == RepositoryLoadingModeData(
        mode=RepositoryTargetMode.FILE,
        data=FileTargetFunction(
            python_file='foo.py',
            fn_name='define_bar_repo',
        )
    )


def test_repo_yaml_module_dynamic_load():
    repository = load_repository_object_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=script_relative_path('repository_module.yml'),
            module_name=None,
            python_file=None,
            fn_name=None,
        )
    ).fn()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_yaml_file_dynamic_load():
    repository = load_repository_object_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=script_relative_path('repository_file.yml'),
            module_name=None,
            python_file=None,
            fn_name=None,
        )
    ).fn()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load():
    repository = load_repository_object_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name='dagster.cli.cli_tests.test_dynamic_loader',
            python_file=None,
            fn_name='define_bar_repo',
        )
    ).fn()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_file_dynamic_load():
    repository = load_repository_object_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name=None,
            python_file=script_relative_path('test_dynamic_loader.py'),
            fn_name='define_bar_repo',
        )
    ).fn()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load_from_pipeline():
    repository = load_repository_object_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name='dagster.cli.cli_tests.test_dynamic_loader',
            python_file=None,
            fn_name='define_foo_pipeline',
        )
    ).fn()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'
    assert repository.get_pipeline('foo').name == 'foo'


def test_repo_file_dynamic_load_from_pipeline():
    repository = load_repository_object_from_target_info(
        RepositoryTargetInfo(
            repository_yaml=None,
            module_name=None,
            python_file=script_relative_path('test_dynamic_loader.py'),
            fn_name='define_foo_pipeline',
        )
    ).fn()

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

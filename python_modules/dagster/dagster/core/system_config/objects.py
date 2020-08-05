'''System-provided config objects and constructors.'''
from collections import namedtuple

from dagster import check
from dagster.core.definitions.executor import ExecutorDefinition
from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.run_config_schema import create_environment_type
from dagster.core.errors import DagsterInvalidConfigError
from dagster.utils import ensure_single_item


class SolidConfig(namedtuple('_SolidConfig', 'config inputs outputs')):
    def __new__(cls, config=None, inputs=None, outputs=None):
        return super(SolidConfig, cls).__new__(
            cls,
            config,
            check.opt_dict_param(inputs, 'inputs', key_type=str),
            check.opt_list_param(outputs, 'outputs', of_type=dict),
        )

    @staticmethod
    def from_dict(config):
        check.dict_param(config, 'config', key_type=str)

        return SolidConfig(
            config=config.get('config'),
            inputs=config.get('inputs') or {},
            outputs=config.get('outputs') or [],
        )


class EmptyIntermediateStoreBackcompatConfig(object):
    '''
    This class is a sentinel object indicating that no intermediate stores have been passed in
    and that the pipeline should instead use system storage to define an intermediate store.
    '''


class EnvironmentConfig(
    namedtuple(
        '_EnvironmentConfig',
        'solids execution storage intermediate_storage resources loggers original_config_dict',
    )
):
    def __new__(
        cls,
        solids=None,
        execution=None,
        storage=None,
        intermediate_storage=None,
        resources=None,
        loggers=None,
        original_config_dict=None,
    ):
        check.opt_inst_param(execution, 'execution', ExecutionConfig)
        check.opt_inst_param(storage, 'storage', StorageConfig)
        check.opt_inst_param(
            intermediate_storage, 'intermediate_storage', IntermediateStorageConfig
        )
        check.opt_dict_param(original_config_dict, 'original_config_dict')
        check.opt_dict_param(resources, 'resources', key_type=str)

        if execution is None:
            execution = ExecutionConfig(None, None)

        return super(EnvironmentConfig, cls).__new__(
            cls,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=SolidConfig),
            execution=execution,
            storage=storage,
            intermediate_storage=intermediate_storage,
            resources=resources,
            loggers=check.opt_dict_param(loggers, 'loggers', key_type=str, value_type=dict),
            original_config_dict=original_config_dict,
        )

    @staticmethod
    def build(pipeline_def, run_config=None, mode=None):
        '''This method validates a given run config against the pipeline config schema. If
        successful, we instantiate an EnvironmentConfig object.

        In case the run_config is invalid, this method raises a DagsterInvalidConfigError
        '''
        from dagster.config.validate import process_config
        from .composite_descent import composite_descent

        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        run_config = check.opt_dict_param(run_config, 'run_config')
        check.opt_str_param(mode, 'mode')

        mode = mode or pipeline_def.get_default_mode_name()
        environment_type = create_environment_type(pipeline_def, mode)

        config_evr = process_config(environment_type, run_config)
        if not config_evr.success:
            raise DagsterInvalidConfigError(
                'Error in config for pipeline {}'.format(pipeline_def.name),
                config_evr.errors,
                run_config,
            )

        config_value = config_evr.value

        config_mapped_resource_configs = config_map_resources(pipeline_def, config_value, mode)
        config_mapped_logger_configs = config_map_loggers(pipeline_def, config_value, mode)
        config_mapped_execution_configs = config_map_executors(pipeline_def, config_value, mode)

        solid_config_dict = composite_descent(pipeline_def, config_value.get('solids', {}))
        # TODO:  replace this with a simple call to from_dict of the config.get when ready to fully deprecate
        temp_intermed = config_value.get('intermediate_storage')
        if config_value.get('storage'):
            if temp_intermed is None:
                temp_intermed = {EmptyIntermediateStoreBackcompatConfig(): {}}

        return EnvironmentConfig(
            solids=solid_config_dict,
            execution=ExecutionConfig.from_dict(config_mapped_execution_configs),
            storage=StorageConfig.from_dict(config_value.get('storage')),
            intermediate_storage=IntermediateStorageConfig.from_dict(temp_intermed),
            loggers=config_mapped_logger_configs,
            original_config_dict=run_config,
            resources=config_mapped_resource_configs,
        )


def config_map_resources(pipeline_def, config_value, mode):
    '''This function executes the config mappings for resources with respect to IConfigMappable.
    It iterates over resource_defs and looks up the corresponding config because resources need to
    be mapped regardless of whether they receive config from run_config.'''

    mode_def = pipeline_def.get_mode_definition(mode)
    resource_configs = config_value.get('resources', {})
    config_mapped_resource_configs = {}
    for resource_key, resource_def in mode_def.resource_defs.items():
        resource_config = resource_configs.get(resource_key, {})
        resource_config_evr = resource_def.apply_config_mapping(resource_config)
        if not resource_config_evr.success:
            raise DagsterInvalidConfigError(
                'Error in config for resource {}'.format(resource_key),
                resource_config_evr.errors,
                resource_config,
            )
        else:
            config_mapped_resource_configs[resource_key] = resource_config_evr.value

    return config_mapped_resource_configs


def config_map_loggers(pipeline_def, config_value, mode):
    '''This function executes the config mappings for loggers with respect to IConfigMappable.
    It uses the `loggers` key on the run_config to determine which loggers will be initialized (and
    thus which ones need config mapping) and then iterates over each, looking up the corresponding
    LoggerDefinition in `mode_def.loggers`.

    The following are the cases of run_config and loggers on mode_def that could emerge
    Run Config                                        Loggers on Mode Def    Behavior                                                          Which Loggers Need Config Mapping?
    -------------------------------------             --------------------   --------------------------------------------------------------    -------------------------------------
    {} or {'loggers': <dict or None>}                 []                     default system loggers with default config                        all loggers on run config (empty set)
    {} or {'loggers': <dict or None>}                 [custom_logger, ...]   default system loggers with default config                        all loggers on run config (empty set)
    {'loggers': {'custom_logger': <dict or None>}}    [custom_logger, ...]   use only the loggers listed in run_config                         all loggers on run config
    {'loggers': {'console': <dict or None>}}          []                     use only the loggers listed in run_config (with default defs)     all loggers on run config

    The behavior of `run_config.loggers` as a source of truth for logger selection comes from:
    python_modules/dagster/dagster/core/execution/context_creation_pipeline.py#create_log_manager
    See that codepath for more info on how the behavior in the above table is implemented. The logic
    in that function is tightly coupled to this one and changes in either path should be confirmed
    in the other.
    '''

    mode_def = pipeline_def.get_mode_definition(mode)
    logger_configs = config_value.get('loggers', {})

    config_mapped_logger_configs = {}

    for logger_key, logger_config in logger_configs.items():
        logger_def = mode_def.loggers.get(logger_key)
        check.inst(logger_def, LoggerDefinition)
        logger_config_evr = logger_def.apply_config_mapping(logger_config)
        if not logger_config_evr.success:
            raise DagsterInvalidConfigError(
                'Error in config for logger {}'.format(logger_key),
                logger_config_evr.errors,
                logger_config,
            )
        else:
            config_mapped_logger_configs[logger_key] = logger_config_evr.value

    return config_mapped_logger_configs


def config_map_executors(pipeline_def, config_value, mode):
    '''This function executes the config mappings for executors with respect to IConfigMappable.
    It calls the ensure_single_item macro on the incoming config and then applies config mapping to
    the result and the first executor_def with the same name on the mode_def.'''

    config = config_value.get('execution')

    check.opt_dict_param(config, 'config', key_type=str)
    if not config:
        return None

    executor_name, executor_config = ensure_single_item(config)

    mode_def = pipeline_def.get_mode_definition(mode)
    executor_def = next(
        (defi for defi in mode_def.executor_defs if defi.name == executor_name), None
    )  # executor_defs are stored in a list and we want to find the def matching name
    check.inst(executor_def, ExecutorDefinition)

    executor_config_evr = executor_def.apply_config_mapping(executor_config)
    if not executor_config_evr.success:
        raise DagsterInvalidConfigError(
            'Error in config for executor {}'.format(executor_name),
            executor_config_evr.errors,
            executor_config,
        )

    return {executor_name: executor_config_evr.value}


class ExecutionConfig(
    namedtuple('_ExecutionConfig', 'execution_engine_name execution_engine_config')
):
    def __new__(cls, execution_engine_name, execution_engine_config):
        return super(ExecutionConfig, cls).__new__(
            cls,
            execution_engine_name=check.opt_str_param(
                execution_engine_name, 'execution_engine_name', 'in_process'
            ),
            execution_engine_config=check.opt_dict_param(
                execution_engine_config, 'execution_engine_config', key_type=str
            ),
        )

    @staticmethod
    def from_dict(config=None):
        check.opt_dict_param(config, 'config', key_type=str)
        if config:
            execution_engine_name, execution_engine_config = ensure_single_item(config)
            return ExecutionConfig(execution_engine_name, execution_engine_config.get('config'))
        return ExecutionConfig(None, None)


class StorageConfig(namedtuple('_FilesConfig', 'system_storage_name system_storage_config')):
    def __new__(cls, system_storage_name, system_storage_config):
        return super(StorageConfig, cls).__new__(
            cls,
            system_storage_name=check.opt_str_param(
                system_storage_name, 'system_storage_name', 'in_memory'
            ),
            system_storage_config=check.opt_dict_param(
                system_storage_config, 'system_storage_config', key_type=str
            ),
        )

    @staticmethod
    def from_dict(config=None):
        check.opt_dict_param(config, 'config', key_type=str)
        if config:
            system_storage_name, system_storage_config = ensure_single_item(config)
            return StorageConfig(system_storage_name, system_storage_config.get('config'))
        return StorageConfig(None, None)


class IntermediateStorageConfig(
    namedtuple('_FilesConfig', 'intermediate_storage_name intermediate_storage_config')
):
    def __new__(cls, intermediate_storage_name, intermediate_storage_config):
        return super(IntermediateStorageConfig, cls).__new__(
            cls,
            intermediate_storage_name=check.opt_inst_param(
                intermediate_storage_name,
                'intermediate_storage_name',
                (str, EmptyIntermediateStoreBackcompatConfig),
                'in_memory',
            ),
            intermediate_storage_config=check.opt_dict_param(
                intermediate_storage_config, 'intermediate_storage_config', key_type=str
            ),
        )

    @staticmethod
    def from_dict(config=None):
        check.opt_dict_param(
            config, 'config', key_type=(str, EmptyIntermediateStoreBackcompatConfig)
        )
        if config:
            intermediate_storage_name, intermediate_storage_config = ensure_single_item(config)
            return IntermediateStorageConfig(
                intermediate_storage_name, intermediate_storage_config.get('config')
            )
        return IntermediateStorageConfig(None, None)

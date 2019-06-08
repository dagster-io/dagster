from collections import namedtuple

from dagster import check

from dagster.core.definitions.dependency import SolidHandle
from dagster.utils import single_item


def construct_solid_dictionary(solid_dict_value, parent_handle=None, config_map=None):
    config_map = config_map or {}
    for name, value in solid_dict_value.items():
        key = SolidHandle(name, None, parent_handle)
        config_map[str(key)] = SolidConfig.from_dict(value)

        # solids implies a composite solid config
        if value.get('solids'):
            construct_solid_dictionary(value['solids'], key, config_map)

    return config_map


class SolidConfig(namedtuple('_SolidConfig', 'config inputs outputs')):
    def __new__(cls, config, inputs=None, outputs=None):
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
            inputs=config.get('inputs', {}),
            outputs=config.get('outputs', []),
        )


class EnvironmentConfig(
    namedtuple(
        '_EnvironmentConfig',
        'solids expectations execution storage resources loggers original_config_dict',
    )
):
    def __new__(
        cls,
        solids=None,
        expectations=None,
        execution=None,
        storage=None,
        resources=None,
        loggers=None,
        original_config_dict=None,
    ):
        check.opt_inst_param(expectations, 'expectations', ExpectationsConfig)
        check.opt_inst_param(execution, 'execution', ExecutionConfig)
        check.opt_inst_param(storage, 'storage', StorageConfig)
        check.opt_dict_param(original_config_dict, 'original_config_dict')
        check.opt_dict_param(resources, 'resources', key_type=str)

        if expectations is None:
            expectations = ExpectationsConfig(evaluate=True)

        if execution is None:
            execution = ExecutionConfig()

        return super(EnvironmentConfig, cls).__new__(
            cls,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=SolidConfig),
            expectations=expectations,
            execution=execution,
            storage=storage,
            resources=resources,
            loggers=check.opt_dict_param(loggers, 'loggers', key_type=str, value_type=dict),
            original_config_dict=original_config_dict,
        )

    @staticmethod
    def from_dict(config):
        check.dict_param(config, 'config', key_type=str)

        return EnvironmentConfig(
            solids=construct_solid_dictionary(config['solids']),
            execution=ExecutionConfig(**config['execution']),
            expectations=ExpectationsConfig(**config['expectations']),
            storage=StorageConfig.from_dict(config.get('storage')),
            loggers=config.get('loggers'),
            original_config_dict=config,
            resources=config.get('resources'),
        )


class ExpectationsConfig(namedtuple('_ExpecationsConfig', 'evaluate')):
    def __new__(cls, evaluate):
        return super(ExpectationsConfig, cls).__new__(
            cls, evaluate=check.bool_param(evaluate, 'evaluate')
        )


class ExecutionConfig(namedtuple('_ExecutionConfig', '')):
    def __new__(cls):
        return super(ExecutionConfig, cls).__new__(cls)


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
            system_storage_name, system_storage_config = single_item(config)
            return StorageConfig(system_storage_name, system_storage_config.get('config'))
        return StorageConfig(None, None)

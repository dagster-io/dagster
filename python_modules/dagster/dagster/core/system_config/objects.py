from collections import namedtuple

from dagster import check

from dagster.core.runs import InMemoryRunStorage, FileSystemRunStorage
from dagster.core.errors import DagsterInvariantViolationError


class SolidConfig(namedtuple('_SolidConfig', 'config inputs outputs')):
    def __new__(cls, config, inputs=None, outputs=None):
        return super(SolidConfig, cls).__new__(
            cls,
            config,
            check.opt_dict_param(inputs, 'inputs', key_type=str),
            check.opt_list_param(outputs, 'outputs', of_type=dict),
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


class ExpectationsConfig(namedtuple('_ExpecationsConfig', 'evaluate')):
    def __new__(cls, evaluate):
        return super(ExpectationsConfig, cls).__new__(
            cls, evaluate=check.bool_param(evaluate, 'evaluate')
        )


class ExecutionConfig(namedtuple('_ExecutionConfig', '')):
    def __new__(cls):
        return super(ExecutionConfig, cls).__new__(cls)


class StorageConfig(namedtuple('_FilesConfig', 'storage_mode storage_config')):
    def __new__(cls, storage_mode, storage_config):
        return super(StorageConfig, cls).__new__(
            cls,
            storage_mode=check.opt_str_param(storage_mode, 'storage_mode'),
            storage_config=check.opt_dict_param(storage_config, 'storage_config', key_type=str),
        )

    def construct_run_storage(self):
        if self.storage_mode == 'filesystem':
            return FileSystemRunStorage()
        elif self.storage_mode == 'in_memory':
            return InMemoryRunStorage()
        elif self.storage_mode == 's3':
            # TODO: Revisit whether we want to use S3 run storage
            return FileSystemRunStorage()
        elif self.storage_mode is None:
            return InMemoryRunStorage()
        else:
            raise DagsterInvariantViolationError(
                'Invalid storage specified {}'.format(self.storage_mode)
            )

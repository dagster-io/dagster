from collections import namedtuple

from dagster import check

DEFAULT_CONTEXT_NAME = 'default'


def _default_persistence_config():
    return {'file': {}}


# lifted from https://bit.ly/2HcQAuv
class ContextConfig(namedtuple('_ContextConfig', 'name config resources persistence')):
    def __new__(cls, name=None, config=None, resources=None, persistence=None):
        return super(ContextConfig, cls).__new__(
            cls,
            check.opt_str_param(name, 'name', DEFAULT_CONTEXT_NAME),
            config,
            check.opt_dict_param(resources, 'resources', key_type=str),
            _default_persistence_config()
            if persistence is None
            else check.dict_param(persistence, 'persistence', key_type=str),
        )


class SolidConfig(namedtuple('_SolidConfig', 'config inputs outputs')):
    def __new__(cls, config, inputs=None, outputs=None):
        return super(SolidConfig, cls).__new__(
            cls,
            config,
            check.opt_dict_param(inputs, 'inputs', key_type=str),
            check.opt_list_param(outputs, 'outputs', of_type=dict),
        )


class EnvironmentConfig(
    namedtuple('_EnvironmentConfig', 'context solids expectations execution original_config_dict')
):
    def __new__(
        cls, solids=None, context=None, expectations=None, execution=None, original_config_dict=None
    ):
        check.opt_inst_param(context, 'context', ContextConfig)
        check.opt_inst_param(expectations, 'expectations', ExpectationsConfig)
        check.opt_inst_param(execution, 'execution', ExecutionConfig)
        check.opt_dict_param(original_config_dict, 'original_config_dict')

        if context is None:
            context = ContextConfig()

        if expectations is None:
            expectations = ExpectationsConfig(evaluate=True)

        if execution is None:
            execution = ExecutionConfig()

        return super(EnvironmentConfig, cls).__new__(
            cls,
            context=context,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=SolidConfig),
            expectations=expectations,
            execution=execution,
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

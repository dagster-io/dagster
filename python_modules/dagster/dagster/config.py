from collections import namedtuple

from dagster import check
from dagster.utils import load_yaml_from_path

DEFAULT_CONTEXT_NAME = 'default'


# lifted from https://bit.ly/2HcQAuv
class Context(namedtuple('ContextData', 'name config')):
    def __new__(cls, name=None, config=None):
        return super(Context, cls).__new__(
            cls,
            check.opt_str_param(name, 'name', DEFAULT_CONTEXT_NAME),
            config,
        )


class Solid(namedtuple('Solid', 'config')):
    def __new__(cls, config):
        return super(Solid, cls).__new__(cls, config)


class Environment(namedtuple('EnvironmentData', 'context solids expectations')):
    def __new__(cls, solids=None, context=None, expectations=None):
        check.opt_inst_param(context, 'context', Context)
        check.opt_inst_param(expectations, 'expectations', Expectations)

        if context is None:
            context = Context()

        if expectations is None:
            expectations = Expectations(evaluate=True)

        return super(Environment, cls).__new__(
            cls,
            context=context,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=Solid),
            expectations=expectations,
        )


class Expectations(namedtuple('ExpectationsData', 'evaluate')):
    def __new__(cls, evaluate):
        return super(Expectations, cls).__new__(
            cls,
            evaluate=check.bool_param(evaluate, 'evaluate'),
        )


def _construct_context(yml_config_object):
    context_obj = check.opt_dict_elem(yml_config_object, 'context')
    if context_obj:
        return Context(
            check.opt_str_elem(context_obj, 'name'),
            context_obj.get('config'),
        )
    else:
        return None


def _coerce_to_list(value):
    if value is None:
        return None
    elif isinstance(value, str):
        return [value]
    elif isinstance(value, list):
        return value

    check.invariant('should not get here')


def _construct_solids(yml_config_object):
    solid_dict = check.opt_dict_elem(yml_config_object, 'solids')
    if solid_dict is None:
        return None

    solid_configs = {}
    for solid_name, solid_yml_object in solid_dict.items():
        config_value = solid_yml_object['config']
        solid_configs[solid_name] = Solid(config_value)

    return solid_configs


def construct_environment(yml_config_object):
    yml_config_object = check.opt_dict_param(yml_config_object, 'yml_config_object')

    return Environment(
        solids=_construct_solids(yml_config_object),
        context=_construct_context(yml_config_object),
    )


def load_environment(path):
    return construct_environment(load_yaml_from_path(path))

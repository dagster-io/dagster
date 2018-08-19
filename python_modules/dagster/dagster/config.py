from collections import (namedtuple, defaultdict)

from dagster import check


# lifted from https://bit.ly/2HcQAuv
class Materialization(namedtuple('MaterializationData', 'solid name args output_name')):
    def __new__(cls, solid, name, args):
        DEFAULT_OUTPUT = 'result'
        return super(Materialization, cls).__new__(
            cls,
            solid=check.str_param(solid, 'solid'),
            name=check.str_param(name, 'name'),
            args=check.dict_param(args, 'args', key_type=str),
            output_name=DEFAULT_OUTPUT,
        )


class Context(namedtuple('ContextData', 'name args')):
    def __new__(cls, name, args):
        return super(Context, cls).__new__(
            cls, check.str_param(name, 'name'), check.dict_param(args, 'args', key_type=str)
        )


class Solid(namedtuple('Solid', 'config_dict')):
    def __new__(cls, config_dict):
        return super(Solid,
                     cls).__new__(cls, check.dict_param(config_dict, 'config_dict', key_type=str))


class Execution(namedtuple('ExecutionData', 'from_solids through_solids')):
    def __new__(cls, from_solids=None, through_solids=None):
        return super(Execution, cls).__new__(
            cls,
            check.opt_list_param(from_solids, 'from_solids', of_type=str),
            check.opt_list_param(through_solids, 'through_solids', of_type=str),
        )

    @staticmethod
    def single_solid(solid_name):
        check.str_param(solid_name, 'solid_name')
        return Execution(from_solids=[solid_name], through_solids=[solid_name])


class Environment(
    namedtuple('EnvironmentData', 'context solids materializations expectations, execution')
):
    def __new__(
        cls, *, solids=None, context=None, materializations=None, expectations=None, execution=None
    ):
        check.opt_inst_param(context, 'context', Context)
        check.opt_inst_param(execution, 'execution', Execution)

        if context is None:
            context = Context(name='default', args={})

        if expectations is None:
            expectations = Expectations(evaluate=True)

        if execution is None:
            execution = Execution()

        return super(Environment, cls).__new__(
            cls,
            context=context,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=Solid),
            materializations=check.opt_list_param(
                materializations, 'materializations', of_type=Materialization
            ),
            expectations=expectations,
            execution=execution,
        )

    @staticmethod
    def empty():
        return Environment()


class Source(namedtuple('SourceData', 'name args')):
    def __new__(cls, name, args):
        return super(Source, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            args=check.dict_param(args, 'args', key_type=str),
        )


class Expectations(namedtuple('ExpectationsData', 'evaluate')):
    def __new__(cls, evaluate):
        return super(Expectations, cls).__new__(
            cls, evaluate=check.bool_param(evaluate, 'evaluate')
        )


def _construct_context(yml_config_object):
    context_obj = check.opt_dict_elem(yml_config_object, 'context')
    if context_obj:
        return Context(check.str_elem(context_obj, 'name'), check.dict_elem(context_obj, 'args'))
    else:
        return None


def _construct_materializations(yml_config_object):
    materializations = [
        Materialization(solid=m['solid'], name=m['name'], args=m['args'])
        for m in check.opt_list_elem(yml_config_object, 'materializations')
    ]
    return materializations


def _coerce_to_list(value):
    if value is None:
        return None
    elif isinstance(value, str):
        return [value]
    elif isinstance(value, list):
        return value

    check.invariant('should not get here')


def _construct_execution(yml_config_object):
    execution_obj = check.opt_dict_elem(yml_config_object, 'execution')
    if execution_obj is None:
        return None

    return Execution(
        from_solids=_coerce_to_list(execution_obj.get('from')),
        through_solids=_coerce_to_list(execution_obj.get('through')),
    )


def _construct_solids(yml_config_object):
    solid_dict = check.opt_dict_elem(yml_config_object, 'solids')
    if solid_dict is None:
        return None

    solid_configs = {}
    for solid_name, solid_yml_object in solid_dict.items():
        config_dict = check.dict_elem(solid_yml_object, 'config')
        solid_configs[solid_name] = Solid(config_dict)

    return solid_configs


def construct_environment(yml_config_object):
    check.dict_param(yml_config_object, 'yml_config_object')

    return Environment(
        solids=_construct_solids(yml_config_object),
        materializations=_construct_materializations(yml_config_object),
        context=_construct_context(yml_config_object),
        execution=_construct_execution(yml_config_object),
    )

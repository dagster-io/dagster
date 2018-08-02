from collections import (namedtuple, defaultdict)

from dagster import check


# lifted from https://bit.ly/2HcQAuv
class Materialization(namedtuple('MaterializationData', 'solid name args')):
    def __new__(cls, solid, name, args):
        return super(Materialization, cls).__new__(
            cls,
            solid=check.str_param(solid, 'solid'),
            name=check.str_param(name, 'name'),
            args=check.dict_param(args, 'args', key_type=str),
        )


class Context(namedtuple('ContextData', 'name args')):
    def __new__(cls, name, args):
        return super(Context, cls).__new__(
            cls, check.str_param(name, 'name'), check.dict_param(args, 'args', key_type=str)
        )


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
    namedtuple('EnvironmentData', 'context sources materializations expectations, execution')
):
    def __new__(
        cls, sources, *, context=None, materializations=None, expectations=None, execution=None
    ):
        check.dict_param(sources, 'sources', key_type=str, value_type=dict)
        for _solid_name, source_dict in sources.items():
            check.dict_param(source_dict, 'source_dict', key_type=str, value_type=Source)

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
            sources=sources,
            materializations=check.opt_list_param(
                materializations, 'materializations', of_type=Materialization
            ),
            expectations=expectations,
            execution=execution,
        )

    @staticmethod
    def empty():
        return Environment(sources={})


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


def _construct_sources(yml_config_object):
    sources = defaultdict(dict)
    sources_obj = check.dict_elem(yml_config_object, 'sources')
    for solid_name, args_yml in sources_obj.items():
        for input_name, source_yml in args_yml.items():
            sources[solid_name][input_name] = Source(
                name=source_yml['name'], args=source_yml['args']
            )
    return sources


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


def construct_environment(yml_config_object):
    check.dict_param(yml_config_object, 'yml_config_object')

    return Environment(
        sources=_construct_sources(yml_config_object),
        materializations=_construct_materializations(yml_config_object),
        context=_construct_context(yml_config_object),
        execution=_construct_execution(yml_config_object),
    )

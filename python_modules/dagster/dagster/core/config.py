from collections import namedtuple

from dagster import check

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


class Environment(namedtuple('EnvironmentData', 'context solids expectations execution')):
    def __new__(cls, solids=None, context=None, expectations=None, execution=None):
        check.opt_inst_param(context, 'context', Context)
        check.opt_inst_param(expectations, 'expectations', Expectations)
        check.opt_inst_param(execution, 'execution', Execution)

        if context is None:
            context = Context()

        if expectations is None:
            expectations = Expectations(evaluate=True)

        if execution is None:
            execution = Execution(serialize_intermediates=False)

        return super(Environment, cls).__new__(
            cls,
            context=context,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=Solid),
            expectations=expectations,
            execution=execution,
        )


class Expectations(namedtuple('ExpectationsData', 'evaluate')):
    def __new__(cls, evaluate):
        return super(Expectations, cls).__new__(
            cls,
            evaluate=check.bool_param(evaluate, 'evaluate'),
        )


class Execution(namedtuple('ExecutionData', 'serialize_intermediates')):
    def __new__(cls, serialize_intermediates):

        return super(Execution, cls).__new__(
            cls,
            check.bool_param(serialize_intermediates, 'serialize_intermediates'),
        )

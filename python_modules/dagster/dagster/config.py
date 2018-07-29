from collections import namedtuple

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


class Environment(namedtuple('EnvironmentData', 'context sources materializations')):
    def __new__(cls, sources, *, context=None, materializations=None):
        check.dict_param(sources, 'sources', key_type=str, value_type=dict)
        for _solid_name, source_dict in sources.items():
            check.dict_param(source_dict, 'source_dict', key_type=str, value_type=Source)

        check.opt_inst_param(context, 'context', Context)

        if context is None:
            context = Context(name='default', args={})

        return super(Environment, cls).__new__(
            cls,
            context=context,
            sources=sources,
            materializations=check.opt_list_param(
                materializations, 'materializations', of_type=Materialization
            ),
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

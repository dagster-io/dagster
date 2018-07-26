from collections import namedtuple

from dagster import check


# lifted from https://bit.ly/2HcQAuv
class Materialization(namedtuple('MaterializationData', 'solid materialization_type args')):
    def __new__(cls, solid, materialization_type, args):
        return super(Materialization, cls).__new__(
            cls,
            solid=check.str_param(solid, 'solid'),
            materialization_type=check.str_param(materialization_type, 'materialization_type'),
            args=check.dict_param(args, 'args', key_type=str),
        )


class Context(namedtuple('Context', 'name args')):
    def __new__(cls, name, args):
        return super(Context, cls).__new__(
            cls, check.str_param(name, 'name'), check.dict_param(args, 'args', key_type=str)
        )


class Environment(namedtuple('EnvironmentData', 'sources context')):
    def __new__(cls, sources, context=None):
        check.dict_param(sources, 'sources', key_type=str, value_type=dict)
        for _solid_name, source_dict in sources.items():
            check.dict_param(source_dict, 'source_dict', key_type=str, value_type=Source)

        if context is None:
            context = Context(name='default', args={})

        return super(Environment, cls).__new__(
            cls,
            sources=sources,
            context=context,
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

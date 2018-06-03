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


class Environment(namedtuple('EnvironmentData', 'input_sources')):
    def __new__(cls, input_sources):
        return super(Environment, cls).__new__(
            cls,
            check.list_param(input_sources, 'input_sources', of_type=Input),
        )

    def input_named(self, input_name):
        for input_source in self.input_sources:
            if input_source.input_name == input_name:
                return input_source
        check.failed(f'Could not find input {input_name} in environment')

    @staticmethod
    def empty():
        return Environment(input_sources=[])


class Input(namedtuple('InputData', 'input_name args source')):
    def __new__(cls, input_name, args, source=None):
        return super(Input, cls).__new__(
            cls,
            input_name=check.str_param(input_name, 'input_name'),
            args=check.dict_param(args, 'args', key_type=str),
            source=check.opt_str_param(source, 'source'),
        )

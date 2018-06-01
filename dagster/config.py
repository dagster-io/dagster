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
            check.list_param(input_sources, 'input_sources', of_type=InputSource),
        )

    def input_source_for_input(self, input_name):
        for input_source in self.input_sources:
            if input_source.input_name == input_name:
                return input_source
        check.failed(f'Could not find input {input_name} in environment')

    @staticmethod
    def empty():
        return Environment(input_sources=[])


class InputSource(namedtuple('InputSourceData', 'input_name source args')):
    def __new__(cls, input_name, source, args):
        return super(InputSource, cls).__new__(
            cls,
            input_name=check.str_param(input_name, 'input_name'),
            source=check.str_param(source, 'source'),
            args=check.dict_param(args, 'args', key_type=str),
        )

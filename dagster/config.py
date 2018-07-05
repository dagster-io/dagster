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


class Environment(namedtuple('EnvironmentData', 'inputs')):
    def __new__(cls, inputs):
        return super(Environment, cls).__new__(
            cls,
            check.list_param(inputs, 'inputs', of_type=Input),
        )

    def input_named(self, input_name):
        for input_ in self.inputs:
            if input_.input_name == input_name:
                return input_
        check.failed(f'Could not find input {input_name} in environment')

    @staticmethod
    def empty():
        return Environment(inputs=[])


class Input(namedtuple('InputData', 'input_name args source')):
    def __new__(cls, input_name, args, source=None):
        return super(Input, cls).__new__(
            cls,
            input_name=check.str_param(input_name, 'input_name'),
            args=check.dict_param(args, 'args', key_type=str),
            source=check.opt_str_param(source, 'source'),
        )

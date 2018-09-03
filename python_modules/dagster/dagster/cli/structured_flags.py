from collections import (defaultdict, namedtuple)
import re

from dagster import check

SingleArgument = namedtuple('SingleArgument', 'value')
_StructuredArguments = namedtuple(
    '_StructuredArguments', 'single_argument named_arguments named_key_arguments'
)
NamedArgument = namedtuple('NamedArgument', 'name value')
NamedKeyArgument = namedtuple('NamedKeyArgument', 'name key value')


class StructuredArguments(_StructuredArguments):
    def _for_name(self, name, key):
        if self.single_argument:
            return self.single_argument.value

        for named_argument in self.named_arguments:
            if named_argument.name == name:
                return named_argument.value

        for nk_arg in self.named_key_arguments:
            if nk_arg.name == name and nk_arg.key == key:
                return nk_arg.value

        return None

    def has_argument(self, name, key):
        check.str_param(name, 'name')
        check.str_param(key, 'key')

        return not self._for_name(name, key) is None

    def argument_for_name(self, name, key):
        check.str_param(name, 'name')
        check.str_param(key, 'key')

        value = self._for_name(name, key)
        if value is None:
            raise StructuredArgumentsError(
                'Could not find name {name} key {key}'.format(name=name, key=key)
            )
        return value


class StructuredArgumentsError(Exception):
    pass


def argument_for_input(inp):
    check.str_param(inp, 'inp')

    named_key_re = r'(\w+)\.(\w+)=(.*)'
    named_key_match = re.match(named_key_re, inp)
    if named_key_match:
        return NamedKeyArgument(
            name=named_key_match.groups()[0],
            key=named_key_match.groups()[1],
            value=named_key_match.groups()[2],
        )

    named_re = r'(\w+)=(.*)'
    named_match = re.match(named_re, inp)
    if named_match:
        return NamedArgument(name=named_match.groups()[0], value=named_match.groups()[1])

    return SingleArgument(value=inp)


def structure_flags(inputs):
    check.list_param(inputs, 'inputs', of_type=str)

    if not inputs:
        return None

    single_argument = None
    named_arguments = []
    named_key_arguments = []

    named_argument_set = set()
    named_argument_key_dict = defaultdict(set)

    for inp in inputs:
        arg = argument_for_input(inp)
        if isinstance(arg, SingleArgument):
            if single_argument is not None:
                raise StructuredArgumentsError('Cannot specify two single args')

            single_argument = arg
        elif isinstance(arg, NamedArgument):
            if single_argument is not None:
                raise StructuredArgumentsError('Single arg must be alone')

            if arg.name in named_argument_set:
                raise StructuredArgumentsError(
                    'Cannot specify name twice: {arg.name}'.format(arg=arg)
                )

            if arg.name in named_argument_key_dict:
                raise StructuredArgumentsError(
                    'Cannot specify name and keyed value: {arg.name}'.format(arg=arg)
                )

            named_arguments.append(arg)
            named_argument_set.add(arg.name)
        elif isinstance(arg, NamedKeyArgument):
            if single_argument is not None:
                raise StructuredArgumentsError('Single arg must be alone')

            if arg.name in named_argument_set:
                raise StructuredArgumentsError(
                    'Cannot specify name twice: {arg.name}'.format(arg=arg)
                )

            if arg.key in named_argument_key_dict[arg.name]:
                raise StructuredArgumentsError(
                    'Cannot specify key ({arg.key}) in name ({arg.name}) twice'.format(arg=arg)
                )

            named_key_arguments.append(arg)
            named_argument_key_dict[arg.name].add(arg.key)
        else:
            check.failed('Not supported type: {type}'.format(type=type(arg)))
    return StructuredArguments(
        single_argument=single_argument,
        named_arguments=named_arguments,
        named_key_arguments=named_key_arguments,
    )

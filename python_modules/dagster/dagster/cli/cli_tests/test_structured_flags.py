import pytest

from dagster.cli.structured_flags import (
    structure_flags,
    SingleArgument,
    StructuredArguments,
    NamedArgument,
    NamedKeyArgument,
    StructuredArgumentsError,
)


def test_structure_flag_empty():
    assert structure_flags([]) is None


def test_structure_flag_single():
    foo_argument = structure_flags(['foo'])
    assert isinstance(foo_argument, StructuredArguments)
    assert isinstance(foo_argument.single_argument, SingleArgument)
    assert not foo_argument.named_arguments
    assert not foo_argument.named_key_arguments
    assert foo_argument.single_argument.value == 'foo'


def test_structure_double_single_fails():
    with pytest.raises(StructuredArgumentsError):
        structure_flags(['foo', 'bar'])

    with pytest.raises(StructuredArgumentsError):
        structure_flags(['foo', 'bar=ad'])

    with pytest.raises(StructuredArgumentsError):
        structure_flags(['foo', 'bar.baz=ad'])


def test_structure_flag_single_named():
    structured_arguments = structure_flags(['foo=bar'])
    assert isinstance(structured_arguments, StructuredArguments)
    assert len(structured_arguments.named_arguments) == 1
    assert not structured_arguments.named_key_arguments

    named_argument = structured_arguments.named_arguments[0]

    assert isinstance(named_argument, NamedArgument)
    assert named_argument.name == 'foo'
    assert named_argument.value == 'bar'


def test_structure_flag_single_named_equal_in_name():
    structured_arguments = structure_flags(['foo=bar='])
    assert isinstance(structured_arguments, StructuredArguments)
    assert len(structured_arguments.named_arguments) == 1
    assert not structured_arguments.named_key_arguments

    named_argument = structured_arguments.named_arguments[0]

    assert isinstance(named_argument, NamedArgument)
    assert named_argument.name == 'foo'
    assert named_argument.value == 'bar='


def test_structure_flag_single_named_key():
    structured_arguments = structure_flags(['foo.baz=bar'])
    assert isinstance(structured_arguments, StructuredArguments)
    assert len(structured_arguments.named_key_arguments) == 1
    assert not structured_arguments.named_arguments

    named_key_argument = structured_arguments.named_key_arguments[0]

    assert isinstance(named_key_argument, NamedKeyArgument)
    assert named_key_argument.name == 'foo'
    assert named_key_argument.key == 'baz'
    assert named_key_argument.value == 'bar'


def test_structure_flag_double_named():
    structured_arguments = structure_flags(['foo=foo_arg', 'bar=bar_arg'])
    assert not structured_arguments.single_argument
    assert len(structured_arguments.named_arguments) == 2
    assert not structured_arguments.named_key_arguments

    assert structured_arguments.named_arguments[0].name == 'foo'
    assert structured_arguments.named_arguments[0].value == 'foo_arg'

    assert structured_arguments.named_arguments[1].name == 'bar'
    assert structured_arguments.named_arguments[1].value == 'bar_arg'


def test_structure_flag_double_dup_fails():
    with pytest.raises(StructuredArgumentsError, match='Cannot specify name twice'):
        structure_flags(['foo=foo_arg', 'foo=bar_arg'])

    with pytest.raises(StructuredArgumentsError):
        structure_flags(['foo=foo_arg', 'foo.key=bar_arg'])

    with pytest.raises(StructuredArgumentsError):
        structure_flags(['foo.key=foo_arg', 'foo=bar_arg'])

    with pytest.raises(StructuredArgumentsError, match='Cannot specify key'):
        structure_flags(['foo.key=foo_arg', 'foo.key=bar_arg'])


def test_structure_two_keys():
    structured_arguments = structure_flags(['foo.key1=key1_arg', 'foo.key2=key2_arg'])
    assert not structured_arguments.single_argument
    assert not structured_arguments.named_arguments
    assert len(structured_arguments.named_key_arguments) == 2

    assert structured_arguments.named_key_arguments[0].name == 'foo'
    assert structured_arguments.named_key_arguments[0].key == 'key1'
    assert structured_arguments.named_key_arguments[0].value == 'key1_arg'

    assert structured_arguments.named_key_arguments[1].name == 'foo'
    assert structured_arguments.named_key_arguments[1].key == 'key2'
    assert structured_arguments.named_key_arguments[1].value == 'key2_arg'

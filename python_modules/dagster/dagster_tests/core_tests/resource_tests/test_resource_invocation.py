from contextlib import contextmanager

import dagster as dg
import pytest


def test_resource_invocation_no_arg():
    @dg.resource
    def basic_resource():
        return 5

    assert basic_resource() == 5


def test_resource_invocation_none_arg():
    @dg.resource
    def basic_resource(_):
        return 5

    assert basic_resource(None) == 5

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            r"Resource initialization function has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        basic_resource()

    @dg.resource
    def basic_resource_arb_context(arb_context):
        return 5

    assert basic_resource_arb_context(None) == 5
    assert basic_resource_arb_context(arb_context=None) == 5

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=r"Resource initialization expected argument 'arb_context'.",
    ):
        assert basic_resource_arb_context(wrong_context=None) == 5


def test_resource_invocation_with_resources():
    @dg.resource(required_resource_keys={"foo"})
    def resource_reqs_resources(init_context):
        return init_context.resources.foo

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=r"Resource has required resources, but no context was provided.",
    ):
        resource_reqs_resources(None)

    context = dg.build_init_resource_context()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"resource with key 'foo' required was not provided.",
    ):
        resource_reqs_resources(context)

    context = dg.build_init_resource_context(resources={"foo": "bar"})
    assert resource_reqs_resources(context) == "bar"


def test_resource_invocation_with_cm_resource():
    teardown_log = []

    @dg.resource
    @contextmanager
    def cm_resource(_):
        try:
            yield "foo"
        finally:
            teardown_log.append("collected")

    with cm_resource(None) as resource_val:
        assert resource_val == "foo"
        assert not teardown_log

    assert teardown_log == ["collected"]


def test_resource_invocation_with_config():
    @dg.resource(config_schema={"foo": str})
    def resource_reqs_config(context):
        assert context.resource_config["foo"] == "bar"
        return 5

    # Ensure that error is raised when we attempt to invoke with a None context
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=r"Resource has required config schema, but no context was provided.",
    ):
        resource_reqs_config(None)

    # Ensure that error is raised when context does not have the required config.
    context = dg.build_init_resource_context()
    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match="Error in config for resource",
    ):
        resource_reqs_config(context)

    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match="Error when applying config mapping for resource",
    ):
        resource_reqs_config.configured({"foobar": "bar"})(None)

    # Ensure that if you configure the respirce, you can provide a none-context.
    result = resource_reqs_config.configured({"foo": "bar"})(None)
    assert result == 5

    result = resource_reqs_config(dg.build_init_resource_context(config={"foo": "bar"}))
    assert result == 5


def test_failing_resource():
    @dg.resource
    def fails(_):
        raise Exception("Oh no!")

    with pytest.raises(Exception, match="Oh no!"):
        fails(None)


def test_resource_invocation_dict_config():
    @dg.resource(config_schema=dict)
    def resource_requires_dict(context):
        assert context.resource_config == {"foo": "bar"}
        return context.resource_config

    assert resource_requires_dict(dg.build_init_resource_context(config={"foo": "bar"})) == {
        "foo": "bar"
    }

    @dg.resource(config_schema=dg.Noneable(dict))
    def resource_noneable_dict(context):
        return context.resource_config

    assert resource_noneable_dict(dg.build_init_resource_context()) is None
    assert resource_noneable_dict(None) is None


def test_resource_invocation_default_config():
    @dg.resource(config_schema={"foo": dg.Field(str, is_required=False, default_value="bar")})
    def resource_requires_config(context):
        assert context.resource_config["foo"] == "bar"
        return context.resource_config["foo"]

    assert resource_requires_config(None) == "bar"

    @dg.resource(config_schema=dg.Field(str, is_required=False, default_value="bar"))
    def resource_requires_config_val(context):
        assert context.resource_config == "bar"
        return context.resource_config

    assert resource_requires_config_val(None) == "bar"

    @dg.resource(
        config_schema={
            "foo": dg.Field(str, is_required=False, default_value="bar"),
            "baz": str,
        }
    )
    def resource_requires_config_partial(context):
        assert context.resource_config["foo"] == "bar"
        assert context.resource_config["baz"] == "bar"
        return context.resource_config["foo"] + context.resource_config["baz"]

    assert (
        resource_requires_config_partial(dg.build_init_resource_context(config={"baz": "bar"}))
        == "barbar"
    )


def test_resource_invocation_kitchen_sink_config():
    @dg.resource(
        config_schema={
            "str_field": str,
            "int_field": int,
            "list_int": [int],
            "list_list_int": [[int]],
            "dict_field": {"a_string": str},
            "list_dict_field": [{"an_int": int}],
            "selector_of_things": dg.Selector(
                {"select_list_dict_field": [{"an_int": int}], "select_int": int}
            ),
            "optional_list_of_optional_string": dg.Noneable([dg.Noneable(str)]),
        }
    )
    def kitchen_sink(context):
        return context.resource_config

    resource_config = {
        "str_field": "kjf",
        "int_field": 2,
        "list_int": [3],
        "list_list_int": [[1], [2, 3]],
        "dict_field": {"a_string": "kdjfkd"},
        "list_dict_field": [{"an_int": 2}, {"an_int": 4}],
        "selector_of_things": {"select_int": 3},
        "optional_list_of_optional_string": ["foo", None],
    }

    assert kitchen_sink(dg.build_init_resource_context(config=resource_config)) == resource_config


def test_resource_dep_no_context():
    @dg.resource(required_resource_keys={"foo"})
    def the_resource():
        pass

    the_resource()

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            r"Attempted to invoke resource with argument, but underlying "
            "function has no context argument. Either specify a context argument on "
            "the resource function, or remove the passed-in argument."
        ),
    ):
        the_resource(None)

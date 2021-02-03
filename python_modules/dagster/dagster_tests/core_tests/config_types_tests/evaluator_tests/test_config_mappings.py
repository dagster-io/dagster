import re

import pytest
from dagster import (
    DagsterConfigMappingFunctionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    Field,
    InputDefinition,
    Int,
    Output,
    String,
    composite_solid,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)


# have to use "pipe" solid since "result_for_solid" doesnt work with composite mappings
# no longer true? refactor these tests?
@lambda_solid(input_defs=[InputDefinition("input_str")])
def pipe(input_str):
    return input_str


@solid(config_schema=Field(String, is_required=False))
def scalar_config_solid(context):
    yield Output(context.solid_config)


@composite_solid(
    config_schema={"override_str": Field(String)},
    config_fn=lambda cfg: {"scalar_config_solid": {"config": cfg["override_str"]}},
)
def wrap():
    return scalar_config_solid()


def test_multiple_overrides_pipeline():
    @composite_solid(
        config_schema={"nesting_override": Field(String)},
        config_fn=lambda cfg: {"wrap": {"config": {"override_str": cfg["nesting_override"]}}},
    )
    def nesting_wrap():
        return wrap()

    @pipeline
    def wrap_pipeline():
        nesting_wrap.alias("outer_wrap")()

    result = execute_pipeline(
        wrap_pipeline,
        {
            "solids": {"outer_wrap": {"config": {"nesting_override": "blah"}}},
            "loggers": {"console": {"config": {"log_level": "ERROR"}}},
        },
    )

    assert result.success
    assert result.result_for_handle("outer_wrap.wrap.scalar_config_solid").output_value() == "blah"


def test_good_override():
    @pipeline
    def wrap_pipeline():
        wrap.alias("do_stuff")()

    result = execute_pipeline(
        wrap_pipeline,
        {
            "solids": {"do_stuff": {"config": {"override_str": "override"}}},
            "loggers": {"console": {"config": {"log_level": "ERROR"}}},
        },
    )

    assert result.success


def test_missing_config():
    @pipeline
    def wrap_pipeline():
        wrap.alias("do_stuff")()

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(wrap_pipeline)

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message == (
        'Missing required config entry "solids" at the root.'
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(wrap_pipeline, {})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message == (
        'Missing required config entry "solids" at the root.'
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(wrap_pipeline, {"solids": {}})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message == (
        'Missing required config entry "do_stuff" at path root:solids.'
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(wrap_pipeline, {"solids": {"do_stuff": {}}})

    assert len(exc_info.value.errors) == 1
    assert (
        exc_info.value.errors[0].message
        == 'Missing required config entry "config" at path root:solids:do_stuff.'
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(wrap_pipeline, {"solids": {"do_stuff": {"config": {}}}})

    assert len(exc_info.value.errors) == 1
    assert (
        exc_info.value.errors[0].message
        == 'Missing required config entry "override_str" at path root:solids:do_stuff:config.'
    )


def test_bad_override():
    @composite_solid(
        config_schema={"does_not_matter": Field(String)},
        config_fn=lambda _cfg: {"scalar_config_solid": {"config": 1234}},
    )
    def bad_wrap():
        return scalar_config_solid()

    @pipeline
    def wrap_pipeline():
        bad_wrap.alias("do_stuff")()

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(
            wrap_pipeline,
            {
                "solids": {"do_stuff": {"config": {"does_not_matter": "blah"}}},
                "loggers": {"console": {"config": {"log_level": "ERROR"}}},
            },
        )

    assert len(exc_info.value.errors) == 1

    message = str(exc_info.value)

    assert 'Solid "do_stuff" with definition "bad_wrap" has a configuration error.' in message
    assert "Error 1: Invalid scalar at path root:scalar_config_solid:config" in message


def test_config_mapper_throws():
    class SomeUserException(Exception):
        pass

    def _config_fn_throws(_cfg):
        raise SomeUserException()

    @composite_solid(config_schema={"does_not_matter": Field(String)}, config_fn=_config_fn_throws)
    def bad_wrap():
        return scalar_config_solid()

    @pipeline
    def wrap_pipeline():
        bad_wrap.alias("do_stuff")()

    with pytest.raises(DagsterConfigMappingFunctionError) as exc_info:
        execute_pipeline(
            wrap_pipeline,
            {"solids": {"do_stuff": {"config": {"does_not_matter": "blah"}}}},
        )

    assert (
        'The config mapping function on the composite solid definition "bad_wrap" at solid '
        '"do_stuff" in pipeline "wrap_pipeline" has thrown an unexpected error during its '
        'execution. The definition is instantiated at stack "do_stuff"'
    ) in str(exc_info.value)


def test_config_mapper_throws_nested():
    class SomeUserException(Exception):
        pass

    def _config_fn_throws(_cfg):
        raise SomeUserException()

    @composite_solid(config_schema={"does_not_matter": Field(String)}, config_fn=_config_fn_throws)
    def bad_wrap():
        return scalar_config_solid()

    @composite_solid
    def container():
        return bad_wrap.alias("layer1")()

    @pipeline
    def wrap_pipeline():
        container.alias("layer0")()

    with pytest.raises(DagsterConfigMappingFunctionError) as exc_info:
        execute_pipeline(
            wrap_pipeline,
            {"solids": {"layer0": {"solids": {"layer1": {"config": {"does_not_matter": "blah"}}}}}},
        )

    assert (
        'The config mapping function on the composite solid definition "bad_wrap" '
        'at solid "layer1" in pipeline "wrap_pipeline" has thrown an unexpected '
        'error during its execution. The definition is instantiated at stack "layer0:layer1".'
    ) in str(exc_info.value)


def test_composite_config_field():
    @solid(config_schema={"inner": Field(String)})
    def inner_solid(context):
        return context.solid_config["inner"]

    @composite_solid(
        config_schema={"override": Int},
        config_fn=lambda cfg: {"inner_solid": {"config": {"inner": str(cfg["override"])}}},
    )
    def test():
        return inner_solid()

    @pipeline
    def test_pipeline():
        test()

    res = execute_pipeline(test_pipeline, {"solids": {"test": {"config": {"override": 5}}}})
    assert res.result_for_handle("test.inner_solid").output_value() == "5"
    assert res.result_for_solid("test").output_value() == "5"


def test_nested_composite_config_field():
    @solid(config_schema={"inner": Field(String)})
    def inner_solid(context):
        return context.solid_config["inner"]

    @composite_solid(
        config_schema={"override": Int},
        config_fn=lambda cfg: {"inner_solid": {"config": {"inner": str(cfg["override"])}}},
    )
    def outer():
        return inner_solid()

    @composite_solid(
        config_schema={"override": Int},
        config_fn=lambda cfg: {"outer": {"config": {"override": cfg["override"]}}},
    )
    def test():
        return outer()

    @pipeline
    def test_pipeline():
        test()

    res = execute_pipeline(test_pipeline, {"solids": {"test": {"config": {"override": 5}}}})
    assert res.success
    assert res.result_for_handle("test.outer.inner_solid").output_value() == "5"
    assert res.result_for_handle("test.outer").output_value() == "5"
    assert res.result_for_solid("test").output_value() == "5"


def test_nested_with_inputs():
    @solid(
        input_defs=[InputDefinition("some_input", String)],
        config_schema={"basic_key": Field(String)},
    )
    def basic(context, some_input):
        yield Output(context.solid_config["basic_key"] + " - " + some_input)

    @composite_solid(
        input_defs=[InputDefinition("some_input", String)],
        config_fn=lambda cfg: {
            "basic": {"config": {"basic_key": "override." + cfg["inner_first"]}}
        },
        config_schema={"inner_first": Field(String)},
    )
    def inner_wrap(some_input):
        return basic(some_input)

    def outer_wrap_fn(cfg):
        return {
            "inner_wrap": {
                "inputs": {"some_input": {"value": "foobar"}},
                "config": {"inner_first": cfg["outer_first"]},
            }
        }

    @composite_solid(config_fn=outer_wrap_fn, config_schema={"outer_first": Field(String)})
    def outer_wrap():
        return inner_wrap()

    @pipeline(name="config_mapping")
    def config_mapping_pipeline():
        pipe(outer_wrap())

    result = execute_pipeline(
        config_mapping_pipeline, {"solids": {"outer_wrap": {"config": {"outer_first": "foo"}}}}
    )

    assert result.success
    assert result.result_for_solid("pipe").output_value() == "override.foo - foobar"


def test_wrap_none_config_and_inputs():
    @solid(
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
        input_defs=[InputDefinition("input_a", String), InputDefinition("input_b", String)],
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.solid_config["config_field_a"],
                context.solid_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @composite_solid
    def wrap_none():
        return basic()

    @pipeline(name="config_mapping")
    def config_mapping_pipeline():
        pipe(wrap_none())

    # Check all good
    result = execute_pipeline(
        config_mapping_pipeline,
        {
            "solids": {
                "wrap_none": {
                    "solids": {
                        "basic": {
                            "inputs": {
                                "input_a": {"value": "set_input_a"},
                                "input_b": {"value": "set_input_b"},
                            },
                            "config": {
                                "config_field_a": "set_config_a",
                                "config_field_b": "set_config_b",
                            },
                        }
                    }
                }
            }
        },
    )
    assert result.success
    assert (
        result.result_for_solid("pipe").output_value()
        == "set_config_a.set_config_b.set_input_a.set_input_b"
    )

    # Check bad input override
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_none": {
                        "solids": {
                            "basic": {
                                "inputs": {
                                    "input_a": {"value": 1234},
                                    "input_b": {"value": "set_input_b"},
                                },
                                "config": {
                                    "config_field_a": "set_config_a",
                                    "config_field_b": "set_config_b",
                                },
                            }
                        }
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:solids:wrap_none:solids:basic:inputs:input_a:value"
        in exc_info.value.errors[0].message
    )

    # Check bad config override
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_none": {
                        "solids": {
                            "basic": {
                                "inputs": {
                                    "input_a": {"value": "set_input_a"},
                                    "input_b": {"value": "set_input_b"},
                                },
                                "config": {
                                    "config_field_a": 1234,
                                    "config_field_b": "set_config_b",
                                },
                            }
                        }
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:solids:wrap_none:solids:basic:config:config_field_a"
        in exc_info.value.errors[0].message
    )


def test_wrap_all_config_no_inputs():
    @solid(
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
        input_defs=[InputDefinition("input_a", String), InputDefinition("input_b", String)],
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.solid_config["config_field_a"],
                context.solid_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @composite_solid(
        input_defs=[InputDefinition("input_a", String), InputDefinition("input_b", String)],
        config_fn=lambda cfg: {
            "basic": {
                "config": {
                    "config_field_a": cfg["config_field_a"],
                    "config_field_b": cfg["config_field_b"],
                }
            }
        },
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
    )
    def wrap_all_config_no_inputs(input_a, input_b):
        return basic(input_a, input_b)

    @pipeline(name="config_mapping")
    def config_mapping_pipeline():
        pipe(wrap_all_config_no_inputs())

    result = execute_pipeline(
        config_mapping_pipeline,
        {
            "solids": {
                "wrap_all_config_no_inputs": {
                    "config": {"config_field_a": "override_a", "config_field_b": "override_b"},
                    "inputs": {
                        "input_a": {"value": "set_input_a"},
                        "input_b": {"value": "set_input_b"},
                    },
                }
            }
        },
    )
    assert result.success
    assert (
        result.result_for_solid("pipe").output_value()
        == "override_a.override_b.set_input_a.set_input_b"
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_all_config_no_inputs": {
                        "config": {"config_field_a": 1234, "config_field_b": "override_b"},
                        "inputs": {
                            "input_a": {"value": "set_input_a"},
                            "input_b": {"value": "set_input_b"},
                        },
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:solids:wrap_all_config_no_inputs:config:config_field_a"
        in exc_info.value.errors[0].message
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_all_config_no_inputs": {
                        "config": {"config_field_a": "override_a", "config_field_b": "override_b"},
                        "inputs": {"input_a": {"value": 1234}, "input_b": {"value": "set_input_b"}},
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:solids:wrap_all_config_no_inputs:inputs:input_a:value"
        in exc_info.value.errors[0].message
    )


def test_wrap_all_config_one_input():
    @solid(
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
        input_defs=[InputDefinition("input_a", String), InputDefinition("input_b", String)],
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.solid_config["config_field_a"],
                context.solid_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @composite_solid(
        input_defs=[InputDefinition("input_a", String)],
        config_fn=lambda cfg: {
            "basic": {
                "config": {
                    "config_field_a": cfg["config_field_a"],
                    "config_field_b": cfg["config_field_b"],
                },
                "inputs": {"input_b": {"value": "set_input_b"}},
            }
        },
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
    )
    def wrap_all_config_one_input(input_a):
        return basic(input_a)

    @pipeline(name="config_mapping")
    def config_mapping_pipeline():
        pipe(wrap_all_config_one_input())

    result = execute_pipeline(
        config_mapping_pipeline,
        {
            "solids": {
                "wrap_all_config_one_input": {
                    "config": {"config_field_a": "override_a", "config_field_b": "override_b"},
                    "inputs": {"input_a": {"value": "set_input_a"}},
                }
            }
        },
    )
    assert result.success
    assert (
        result.result_for_solid("pipe").output_value()
        == "override_a.override_b.set_input_a.set_input_b"
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_all_config_one_input": {
                        "config": {"config_field_a": 1234, "config_field_b": "override_b"},
                        "inputs": {"input_a": {"value": "set_input_a"}},
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:solids:wrap_all_config_one_input:config:config_field_a."
        in exc_info.value.errors[0].message
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_all_config_one_input": {
                        "config": {"config_field_a": "override_a", "config_field_b": "override_b"},
                        "inputs": {"input_a": {"value": 1234}},
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:solids:wrap_all_config_one_input:inputs:input_a:value"
        in exc_info.value.errors[0].message
    )


def test_wrap_all_config_and_inputs():
    @solid(
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
        input_defs=[InputDefinition("input_a", String), InputDefinition("input_b", String)],
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.solid_config["config_field_a"],
                context.solid_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @composite_solid(
        config_fn=lambda cfg: {
            "basic": {
                "config": {
                    "config_field_a": cfg["config_field_a"],
                    "config_field_b": cfg["config_field_b"],
                },
                "inputs": {
                    "input_a": {"value": "override_input_a"},
                    "input_b": {"value": "override_input_b"},
                },
            }
        },
        config_schema={"config_field_a": Field(String), "config_field_b": Field(String)},
    )
    def wrap_all():
        return basic()

    @pipeline(name="config_mapping")
    def config_mapping_pipeline():
        pipe(wrap_all())

    result = execute_pipeline(
        config_mapping_pipeline,
        {
            "solids": {
                "wrap_all": {
                    "config": {"config_field_a": "override_a", "config_field_b": "override_b"}
                }
            }
        },
    )

    assert result.success
    assert (
        result.result_for_solid("pipe").output_value()
        == "override_a.override_b.override_input_a.override_input_b"
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = execute_pipeline(
            config_mapping_pipeline,
            {
                "solids": {
                    "wrap_all": {
                        "config": {
                            "config_field_a": "override_a",
                            "this_key_doesnt_exist": "override_b",
                        }
                    }
                }
            },
        )

    assert len(exc_info.value.errors) == 2
    assert exc_info.value.errors[0].message == (
        'Received unexpected config entry "this_key_doesnt_exist" at path root:solids:wrap_all:config. '
        'Expected: "{ config_field_a: String config_field_b: String }".'
    )

    assert (
        exc_info.value.errors[1].message
        == 'Missing required config entry "config_field_b" at path root:solids:wrap_all:config.'
    )


def test_empty_config():
    # Testing that this definition does *not* raise
    # See: https://github.com/dagster-io/dagster/issues/1606
    @composite_solid(
        config_fn=lambda _: {"scalar_config_solid": {"config": "an input"}}, config_schema={}
    )
    def wrap_solid():  # pylint: disable=unused-variable
        return scalar_config_solid()

    @pipeline
    def wrap_pipeline():
        wrap_solid()

    res = execute_pipeline(wrap_pipeline, run_config={"solids": {}})
    assert res.result_for_solid("wrap_solid").output_values == {"result": "an input"}

    res = execute_pipeline(wrap_pipeline)
    assert res.result_for_solid("wrap_solid").output_values == {"result": "an input"}


def test_nested_empty_config():
    @composite_solid(
        config_fn=lambda _: {"scalar_config_solid": {"config": "an input"}}, config_schema={}
    )
    def wrap_solid():  # pylint: disable=unused-variable
        return scalar_config_solid()

    @composite_solid
    def double_wrap():
        return wrap_solid()

    @pipeline
    def wrap_pipeline():
        double_wrap()

    res = execute_pipeline(wrap_pipeline, run_config={"solids": {}})
    assert res.result_for_solid("double_wrap").output_values == {"result": "an input"}

    res = execute_pipeline(wrap_pipeline)
    assert res.result_for_solid("double_wrap").output_values == {"result": "an input"}


def test_nested_empty_config_input():
    @lambda_solid
    def number(num):
        return num

    @composite_solid(
        config_fn=lambda _: {"number": {"inputs": {"num": {"value": 4}}}}, config_schema={}
    )
    def wrap_solid():  # pylint: disable=unused-variable
        return number()

    @composite_solid
    def double_wrap(num):
        number(num)
        return wrap_solid()

    @pipeline
    def wrap_pipeline():
        double_wrap()

    res = execute_pipeline(
        wrap_pipeline,
        run_config={"solids": {"double_wrap": {"inputs": {"num": {"value": 2}}}}},
    )
    assert res.result_for_handle("double_wrap.number").output_value() == 2
    assert res.result_for_solid("double_wrap").output_values == {"result": 4}


def test_bad_solid_def():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "@composite_solid 'config_only' defines a configuration schema but does not define a "
            "configuration function."
        ),
    ):

        @composite_solid(config_schema={"test": Field(String)})
        def config_only():  # pylint: disable=unused-variable
            scalar_config_solid()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "@composite_solid 'config_fn_only' defines a configuration function <lambda> but does not "
            "define a configuration schema."
        ),
    ):

        @composite_solid(config_fn=lambda _cfg: {})
        def config_fn_only():  # pylint: disable=unused-variable
            scalar_config_solid()

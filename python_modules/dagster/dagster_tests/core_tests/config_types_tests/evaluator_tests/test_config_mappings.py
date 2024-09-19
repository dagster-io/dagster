import pytest
from dagster import (
    ConfigMapping,
    DagsterConfigMappingFunctionError,
    DagsterInvalidConfigError,
    Field,
    In,
    Int,
    Output,
    String,
    graph,
    job,
    op,
)


@op
def pipe(input_str):
    return input_str


@op(config_schema=Field(String, is_required=False))
def scalar_config_op(context):
    yield Output(context.op_config)


@graph(
    config=ConfigMapping(
        config_schema={"override_str": Field(String)},
        config_fn=lambda cfg: {"scalar_config_op": {"config": cfg["override_str"]}},
    )
)
def wrap():
    return scalar_config_op()


def test_multiple_overrides_job():
    @graph(
        config=ConfigMapping(
            config_schema={"nesting_override": Field(String)},
            config_fn=lambda cfg: {"wrap": {"config": {"override_str": cfg["nesting_override"]}}},
        )
    )
    def nesting_wrap():
        return wrap()

    @job
    def wrap_job():
        nesting_wrap.alias("outer_wrap")()

    result = wrap_job.execute_in_process(
        {
            "ops": {"outer_wrap": {"config": {"nesting_override": "blah"}}},
            "loggers": {"console": {"config": {"log_level": "ERROR"}}},
        },
    )

    assert result.success
    assert result.output_for_node("outer_wrap.wrap.scalar_config_op") == "blah"


def test_good_override():
    @job
    def wrap_job():
        wrap.alias("do_stuff")()

    result = wrap_job.execute_in_process(
        {
            "ops": {"do_stuff": {"config": {"override_str": "override"}}},
            "loggers": {"console": {"config": {"log_level": "ERROR"}}},
        },
    )

    assert result.success


def test_missing_config():
    @job
    def wrap_job():
        wrap.alias("do_stuff")()

    expected_suggested_config = {"ops": {"do_stuff": {"config": {"override_str": "..."}}}}
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        wrap_job.execute_in_process()

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "ops" at the root.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        wrap_job.execute_in_process({})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "ops" at the root.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    expected_suggested_config = expected_suggested_config["ops"]
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        wrap_job.execute_in_process({"ops": {}})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "do_stuff" at path root:ops.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    expected_suggested_config = expected_suggested_config["do_stuff"]
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        wrap_job.execute_in_process({"ops": {"do_stuff": {}}})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "config" at path root:ops:do_stuff.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    expected_suggested_config = expected_suggested_config["config"]
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        wrap_job.execute_in_process({"ops": {"do_stuff": {"config": {}}}})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "override_str" at path root:ops:do_stuff:config.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message


def test_bad_override():
    @graph(
        config=ConfigMapping(
            config_schema={"does_not_matter": Field(String)},
            config_fn=lambda _cfg: {"scalar_config_op": {"config": 1234}},
        )
    )
    def bad_wrap():
        return scalar_config_op()

    @job
    def wrap_job():
        bad_wrap.alias("do_stuff")()

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        wrap_job.execute_in_process(
            {
                "ops": {"do_stuff": {"config": {"does_not_matter": "blah"}}},
                "loggers": {"console": {"config": {"log_level": "ERROR"}}},
            },
        )

    assert len(exc_info.value.errors) == 1

    message = str(exc_info.value)

    assert 'Op "do_stuff" with definition "bad_wrap" has a configuration error.' in message
    assert "Error 1: Invalid scalar at path root:scalar_config_op:config" in message


def test_config_mapper_throws():
    class SomeUserException(Exception):
        pass

    def _config_fn_throws(_cfg):
        raise SomeUserException()

    @graph(
        config=ConfigMapping(
            config_schema={"does_not_matter": Field(String)},
            config_fn=_config_fn_throws,
        )
    )
    def bad_wrap():
        return scalar_config_op()

    @job
    def wrap_job():
        bad_wrap.alias("do_stuff")()

    with pytest.raises(
        DagsterConfigMappingFunctionError,
        match=(
            "The config mapping function on graph 'do_stuff' "
            "in job 'wrap_job' has thrown an unexpected error during its "
            'execution. The definition is instantiated at stack "do_stuff"'
        ),
    ):
        wrap_job.execute_in_process(
            {"ops": {"do_stuff": {"config": {"does_not_matter": "blah"}}}},
        )

    @graph
    def wrap_invocations():
        bad_wrap()

    # Workaround to check error message for job since GraphDefinition currently does not accept
    # config mapping: https://github.com/dagster-io/dagster/issues/4831
    with pytest.raises(
        DagsterConfigMappingFunctionError,
        match=(
            "The config mapping function on graph 'bad_wrap' "
            "in job 'wrap_invocations' has thrown an unexpected error during its "
            'execution. The definition is instantiated at stack "bad_wrap"'
        ),
    ):
        wrap_invocations.to_job().execute_in_process(
            run_config={"ops": {"bad_wrap": {"config": {"does_not_matter": "blah"}}}}
        )


def test_config_mapper_throws_nested():
    class SomeUserException(Exception):
        pass

    def _config_fn_throws(_cfg):
        raise SomeUserException()

    @graph(
        config=ConfigMapping(
            config_schema={"does_not_matter": Field(String)},
            config_fn=_config_fn_throws,
        )
    )
    def bad_wrap():
        return scalar_config_op()

    @graph
    def container():
        return bad_wrap.alias("layer1")()

    @job
    def wrap_job():
        container.alias("layer0")()

    with pytest.raises(DagsterConfigMappingFunctionError) as exc_info:
        wrap_job.execute_in_process(
            {"ops": {"layer0": {"ops": {"layer1": {"config": {"does_not_matter": "blah"}}}}}},
        )

    assert (
        "The config mapping function on graph 'layer1' "
        "in job 'wrap_job' has thrown an unexpected "
        'error during its execution. The definition is instantiated at stack "layer0:layer1".'
        in str(exc_info.value)
    )


def test_composite_config_field():
    @op(config_schema={"inner": Field(String)})
    def inner_op(context):
        return context.op_config["inner"]

    @graph(
        config=ConfigMapping(
            config_schema={"override": Int},
            config_fn=lambda cfg: {"inner_op": {"config": {"inner": str(cfg["override"])}}},
        )
    )
    def test():
        return inner_op()

    @job
    def test_job():
        test()

    res = test_job.execute_in_process({"ops": {"test": {"config": {"override": 5}}}})
    assert res.output_for_node("test.inner_op") == "5"
    assert res.output_for_node("test") == "5"


def test_nested_composite_config_field():
    @op(config_schema={"inner": Field(String)})
    def inner_op(context):
        return context.op_config["inner"]

    @graph(
        config=ConfigMapping(
            config_schema={"override": Int},
            config_fn=lambda cfg: {"inner_op": {"config": {"inner": str(cfg["override"])}}},
        )
    )
    def outer():
        return inner_op()

    @graph(
        config=ConfigMapping(
            config_schema={"override": Int},
            config_fn=lambda cfg: {"outer": {"config": {"override": cfg["override"]}}},
        )
    )
    def test():
        return outer()

    @job
    def test_job():
        test()

    res = test_job.execute_in_process({"ops": {"test": {"config": {"override": 5}}}})
    assert res.success
    assert res.output_for_node("test.outer.inner_op") == "5"
    assert res.output_for_node("test.outer") == "5"
    assert res.output_for_node("test") == "5"


def test_nested_with_inputs():
    @op(
        ins={"some_input": In(String)},
        config_schema={"basic_key": Field(String)},
    )
    def basic(context, some_input):
        yield Output(context.op_config["basic_key"] + " - " + some_input)

    @graph(
        config=ConfigMapping(
            config_fn=lambda cfg: {
                "basic": {"config": {"basic_key": "override." + cfg["inner_first"]}}
            },
            config_schema={"inner_first": Field(String)},
        )
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

    @graph(
        config=ConfigMapping(
            config_schema={"outer_first": Field(String)},
            config_fn=outer_wrap_fn,
        )
    )
    def outer_wrap():
        return inner_wrap()

    @job(name="config_mapping")
    def config_mapping_job():
        pipe(outer_wrap())

    result = config_mapping_job.execute_in_process(
        {"ops": {"outer_wrap": {"config": {"outer_first": "foo"}}}},
    )

    assert result.success
    assert result.output_for_node("pipe") == "override.foo - foobar"


def test_wrap_none_config_and_inputs():
    @op(
        config_schema={
            "config_field_a": Field(String),
            "config_field_b": Field(String),
        },
        ins={"input_a": In(String), "input_b": In(String)},
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.op_config["config_field_a"],
                context.op_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @graph
    def wrap_none():
        return basic()

    @job(name="config_mapping")
    def config_mapping_job():
        pipe(wrap_none())

    # Check all good
    result = config_mapping_job.execute_in_process(
        {
            "ops": {
                "wrap_none": {
                    "ops": {
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
    assert result.output_for_node("pipe") == "set_config_a.set_config_b.set_input_a.set_input_b"

    # Check bad input override
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
                    "wrap_none": {
                        "ops": {
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
        "Invalid scalar at path root:ops:wrap_none:ops:basic:inputs:input_a:value"
        in exc_info.value.errors[0].message
    )

    # Check bad config override
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
                    "wrap_none": {
                        "ops": {
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
        "Invalid scalar at path root:ops:wrap_none:ops:basic:config:config_field_a"
        in exc_info.value.errors[0].message
    )


def test_wrap_all_config_no_inputs():
    @op(
        config_schema={
            "config_field_a": Field(String),
            "config_field_b": Field(String),
        },
        ins={"input_a": In(String), "input_b": In(String)},
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.op_config["config_field_a"],
                context.op_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @graph(
        config=ConfigMapping(
            config_fn=lambda cfg: {
                "basic": {
                    "config": {
                        "config_field_a": cfg["config_field_a"],
                        "config_field_b": cfg["config_field_b"],
                    }
                }
            },
            config_schema={
                "config_field_a": Field(String),
                "config_field_b": Field(String),
            },
        )
    )
    def wrap_all_config_no_inputs(input_a, input_b):
        return basic(input_a, input_b)

    @job(name="config_mapping")
    def config_mapping_job():
        pipe(wrap_all_config_no_inputs())

    result = config_mapping_job.execute_in_process(
        {
            "ops": {
                "wrap_all_config_no_inputs": {
                    "config": {
                        "config_field_a": "override_a",
                        "config_field_b": "override_b",
                    },
                    "inputs": {
                        "input_a": {"value": "set_input_a"},
                        "input_b": {"value": "set_input_b"},
                    },
                }
            }
        },
    )
    assert result.success
    assert result.output_for_node("pipe") == "override_a.override_b.set_input_a.set_input_b"

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
                    "wrap_all_config_no_inputs": {
                        "config": {
                            "config_field_a": 1234,
                            "config_field_b": "override_b",
                        },
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
        "Invalid scalar at path root:ops:wrap_all_config_no_inputs:config:config_field_a"
        in exc_info.value.errors[0].message
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
                    "wrap_all_config_no_inputs": {
                        "config": {
                            "config_field_a": "override_a",
                            "config_field_b": "override_b",
                        },
                        "inputs": {
                            "input_a": {"value": 1234},
                            "input_b": {"value": "set_input_b"},
                        },
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:ops:wrap_all_config_no_inputs:inputs:input_a:value"
        in exc_info.value.errors[0].message
    )


def test_wrap_all_config_one_input():
    @op(
        config_schema={
            "config_field_a": Field(String),
            "config_field_b": Field(String),
        },
        ins={"input_a": In(String), "input_b": In(String)},
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.op_config["config_field_a"],
                context.op_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @graph(
        config=ConfigMapping(
            config_fn=lambda cfg: {
                "basic": {
                    "config": {
                        "config_field_a": cfg["config_field_a"],
                        "config_field_b": cfg["config_field_b"],
                    },
                    "inputs": {"input_b": {"value": "set_input_b"}},
                }
            },
            config_schema={
                "config_field_a": Field(String),
                "config_field_b": Field(String),
            },
        )
    )
    def wrap_all_config_one_input(input_a):
        return basic(input_a)

    @job(name="config_mapping")
    def config_mapping_job():
        pipe(wrap_all_config_one_input())

    result = config_mapping_job.execute_in_process(
        {
            "ops": {
                "wrap_all_config_one_input": {
                    "config": {
                        "config_field_a": "override_a",
                        "config_field_b": "override_b",
                    },
                    "inputs": {"input_a": {"value": "set_input_a"}},
                }
            }
        },
    )
    assert result.success
    assert result.output_for_node("pipe") == "override_a.override_b.set_input_a.set_input_b"

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
                    "wrap_all_config_one_input": {
                        "config": {
                            "config_field_a": 1234,
                            "config_field_b": "override_b",
                        },
                        "inputs": {"input_a": {"value": "set_input_a"}},
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:ops:wrap_all_config_one_input:config:config_field_a."
        in exc_info.value.errors[0].message
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
                    "wrap_all_config_one_input": {
                        "config": {
                            "config_field_a": "override_a",
                            "config_field_b": "override_b",
                        },
                        "inputs": {"input_a": {"value": 1234}},
                    }
                }
            },
        )
    assert len(exc_info.value.errors) == 1
    assert (
        "Invalid scalar at path root:ops:wrap_all_config_one_input:inputs:input_a:value"
        in exc_info.value.errors[0].message
    )


def test_wrap_all_config_and_inputs():
    @op(
        config_schema={
            "config_field_a": Field(String),
            "config_field_b": Field(String),
        },
        ins={"input_a": In(String), "input_b": In(String)},
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.op_config["config_field_a"],
                context.op_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @graph(
        config=ConfigMapping(
            config_schema={
                "config_field_a": Field(String),
                "config_field_b": Field(String),
            },
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
        )
    )
    def wrap_all():
        return basic()

    @job(name="config_mapping")
    def config_mapping_job():
        pipe(wrap_all())

    result = config_mapping_job.execute_in_process(
        {
            "ops": {
                "wrap_all": {
                    "config": {
                        "config_field_a": "override_a",
                        "config_field_b": "override_b",
                    }
                }
            }
        },
    )

    assert result.success
    assert (
        result.output_for_node("pipe") == "override_a.override_b.override_input_a.override_input_b"
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        result = config_mapping_job.execute_in_process(
            {
                "ops": {
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
    assert (
        exc_info.value.errors[0].message
        == 'Received unexpected config entry "this_key_doesnt_exist" at path'
        ' root:ops:wrap_all:config. Expected: "{ config_field_a: String config_field_b:'
        ' String }".'
    )

    expected_suggested_config = {"config_field_b": "..."}
    assert exc_info.value.errors[1].message.startswith(
        'Missing required config entry "config_field_b" at path root:ops:wrap_all:config.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[1].message


def test_empty_config():
    # Testing that this definition does *not* raise
    # See: https://github.com/dagster-io/dagster/issues/1606
    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda _: {"scalar_config_op": {"config": "an input"}},
        )
    )
    def wrap_graph():
        return scalar_config_op()

    @job
    def wrap_job():
        wrap_graph()

    res = wrap_job.execute_in_process(run_config={"ops": {}})
    assert res.output_for_node("wrap_graph") == "an input"

    res = wrap_job.execute_in_process()
    assert res.output_for_node("wrap_graph") == "an input"


def test_nested_empty_config():
    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda _: {"scalar_config_op": {"config": "an input"}},
        )
    )
    def wrap_graph():
        return scalar_config_op()

    @graph
    def double_wrap():
        return wrap_graph()

    @job
    def wrap_job():
        double_wrap()

    res = wrap_job.execute_in_process(run_config={"ops": {}})
    assert res.output_for_node("double_wrap") == "an input"

    res = wrap_job.execute_in_process()
    assert res.output_for_node("double_wrap") == "an input"


def test_nested_empty_config_input():
    @op
    def number(num):
        return num

    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda _: {"number": {"inputs": {"num": {"value": 4}}}},
        )
    )
    def wrap_graph():
        return number()

    @graph
    def double_wrap(num):
        number(num)
        return wrap_graph()

    @job
    def wrap_job():
        double_wrap()

    res = wrap_job.execute_in_process(
        run_config={"ops": {"double_wrap": {"inputs": {"num": {"value": 2}}}}},
    )
    assert res.output_for_node("double_wrap.number") == 2
    assert res.output_for_node("double_wrap") == 4


def test_default_config_schema():
    @graph(config=ConfigMapping(config_fn=lambda _cfg: {}))
    def config_fn_only():
        scalar_config_op()

    @job
    def wrap_job():
        config_fn_only()

    result = wrap_job.execute_in_process(
        {"ops": {"config_fn_only": {"config": {"override_str": "override"}}}},
    )

    assert result.success

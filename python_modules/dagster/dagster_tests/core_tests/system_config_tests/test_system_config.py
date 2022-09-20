import re

from dagster import (
    Any,
    DependencyDefinition,
    Field,
    GraphDefinition,
    In,
    Int,
    NodeInvocation,
    Out,
    ResourceDefinition,
    Shape,
    String,
    job,
    op,
)
from dagster._config import ConfigTypeKind, process_config
from dagster._core.definitions import create_run_config_schema
from dagster._core.definitions.run_config import (
    RunConfigSchemaCreationData,
    define_solid_dictionary_cls,
)
from dagster._core.system_config.objects import ResolvedRunConfig, ResourceConfig, SolidConfig
from dagster._legacy import OutputDefinition, SolidDefinition
from dagster._loggers import default_loggers


def create_creation_data(job_def):
    return RunConfigSchemaCreationData(
        job_def.name,
        job_def.solids,
        job_def.dependency_structure,
        job_def.mode_definition,
        logger_defs=default_loggers(),
        ignored_solids=[],
        required_resources=set(),
        is_using_graph_job_op_apis=job_def.is_job,
        direct_inputs=job_def._input_values  # pylint: disable = protected-access
        if job_def.is_job
        else {},
        asset_layer=job_def.asset_layer,
    )


def create_run_config_schema_type(job_def):
    schema = create_run_config_schema(pipeline_def=job_def, mode=None)
    return schema.config_type


def test_all_types_provided():
    job_def = GraphDefinition(name="pipeline", node_defs=[],).to_job(
        resource_defs={
            "some_resource": ResourceDefinition(
                lambda _: None,
                config_schema={
                    "with_default_int": Field(Int, is_required=False, default_value=23434)
                },
            )
        },
    )

    run_config_schema = create_run_config_schema(job_def)

    all_types = list(run_config_schema.all_config_types())

    matching_types = [
        tt
        for tt in all_types
        if tt.kind == ConfigTypeKind.STRICT_SHAPE and "with_default_int" in tt.fields.keys()
    ]
    assert len(matching_types) == 1


def test_provided_default_on_resources_config():
    @op(
        name="some_op",
        ins={},
        out={},
        required_resource_keys={"some_resource"},
    )
    def some_op(_):
        return None

    @job(
        resource_defs={
            "some_resource": ResourceDefinition(
                resource_fn=lambda _: None,
                config_schema={
                    "with_default_int": Field(Int, is_required=False, default_value=23434)
                },
            )
        }
    )
    def job_def():
        some_op()

    env_type = create_run_config_schema_type(job_def)
    some_resource_field = env_type.fields["resources"].config_type.fields["some_resource"]
    assert some_resource_field.is_required is False

    some_resource_config_field = some_resource_field.config_type.fields["config"]
    assert some_resource_config_field.is_required is False
    assert some_resource_config_field.default_value == {"with_default_int": 23434}

    assert some_resource_field.default_value == {"config": {"with_default_int": 23434}}

    value = ResolvedRunConfig.build(job_def, {})
    assert value.resources == {
        "some_resource": ResourceConfig({"with_default_int": 23434}),
    }


def test_default_environment():
    @op(name="some_op", ins={}, out={})
    def some_op(_):
        return None

    @job
    def job_def():
        some_op()

    assert ResolvedRunConfig.build(job_def, {})


def test_solid_config():
    solid_config_type = Shape({"config": Field(Int)})
    solid_inst = process_config(solid_config_type, {"config": 1})
    assert solid_inst.value["config"] == 1


def test_solid_dictionary_type():
    job_def = define_test_solids_config_pipeline()

    env_obj = ResolvedRunConfig.build(
        job_def,
        {
            "ops": {
                "int_config_op": {"config": 1},
                "string_config_op": {"config": "bar"},
            },
        },
    )

    value = env_obj.solids

    assert set(["int_config_op", "string_config_op"]) == set(value.keys())
    assert value == {
        "int_config_op": SolidConfig.from_dict({"config": 1}),
        "string_config_op": SolidConfig.from_dict({"config": "bar"}),
    }


def define_test_solids_config_pipeline():
    @op(
        name="int_config_op",
        config_schema=Field(Int, is_required=False),
        ins={},
        out={},
    )
    def int_config_op(_):
        return None

    @op(
        name="string_config_op",
        config_schema=Field(String, is_required=False),
        ins={},
        out={},
    )
    def string_config_op(_):
        return None

    @job
    def job_def():
        int_config_op()
        string_config_op()

    return job_def


def assert_has_fields(dtype, *fields):
    return set(dtype.fields.keys()) == set(fields)


def test_solid_configs_defaults():
    env_type = create_run_config_schema_type(define_test_solids_config_pipeline())

    solids_field = env_type.fields["ops"]

    assert_has_fields(solids_field.config_type, "int_config_op", "string_config_op")

    int_solid_field = solids_field.config_type.fields["int_config_op"]

    assert int_solid_field.is_required is False
    # TODO: this is the test case the exposes the default dodginess
    # https://github.com/dagster-io/dagster/issues/1990
    assert int_solid_field.default_provided

    assert_has_fields(int_solid_field.config_type, "config")

    int_solid_config_field = int_solid_field.config_type.fields["config"]

    assert int_solid_config_field.is_required is False
    assert not int_solid_config_field.default_provided


def test_solid_dictionary_some_no_config():
    @op(name="int_config_op", config_schema=Int, ins={}, out={})
    def int_config_op(_):
        return None

    @op(name="no_config_op", ins={}, out={})
    def no_config_op(_):
        return None

    @job
    def job_def():
        int_config_op()
        no_config_op()

    env = ResolvedRunConfig.build(job_def, {"ops": {"int_config_op": {"config": 1}}})

    assert {"int_config_op", "no_config_op"} == set(env.solids.keys())
    assert env.solids == {
        "int_config_op": SolidConfig.from_dict({"config": 1}),
        "no_config_op": SolidConfig.from_dict({}),
    }


def test_whole_environment():
    job_def = GraphDefinition(
        name="some_pipeline",
        node_defs=[
            SolidDefinition(
                name="int_config_op",
                config_schema=Int,
                input_defs=[],
                output_defs=[OutputDefinition()],
                required_resource_keys={"test_resource"},
                compute_fn=lambda *args: None,
            ),
            SolidDefinition(
                name="no_config_op",
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *args: None,
            ),
        ],
    ).to_job(
        resource_defs={
            "test_resource": ResourceDefinition(resource_fn=lambda _: None, config_schema=Any)
        },
    )

    env = ResolvedRunConfig.build(
        job_def,
        {
            "resources": {"test_resource": {"config": 1}},
            "ops": {"int_config_op": {"config": 123}},
        },
    )

    assert isinstance(env, ResolvedRunConfig)
    assert env.solids == {
        "int_config_op": SolidConfig.from_dict({"config": 123}),
        "no_config_op": SolidConfig.from_dict({}),
    }
    assert env.resources == {
        "test_resource": ResourceConfig(1),
        "io_manager": ResourceConfig(None),
    }


def test_solid_config_error():
    job_def = define_test_solids_config_pipeline()
    solid_dict_type = define_solid_dictionary_cls(
        solids=job_def.solids,
        ignored_solids=None,
        dependency_structure=job_def.dependency_structure,
        parent_handle=None,
        resource_defs={},
        is_using_graph_job_op_apis=False,
        asset_layer=job_def.asset_layer,
    )

    int_solid_config_type = solid_dict_type.fields["int_config_op"].config_type

    res = process_config(int_solid_config_type, {"notconfig": 1})
    assert not res.success
    assert re.match('Received unexpected config entry "notconfig"', res.errors[0].message)

    res = process_config(int_solid_config_type, 1)
    assert not res.success


def test_optional_solid_with_no_config():
    def _assert_config_none(context, value):
        assert context.op_config is value

    job_def = GraphDefinition(
        name="some_pipeline",
        node_defs=[
            SolidDefinition(
                name="int_config_op",
                config_schema=Int,
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            ),
            SolidDefinition(
                name="no_config_op",
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, None),
            ),
        ],
    ).to_job()

    assert job_def.execute_in_process({"ops": {"int_config_op": {"config": 234}}}).success


def test_optional_solid_with_optional_scalar_config():
    def _assert_config_none(context, value):
        assert context.op_config is value

    job_def = GraphDefinition(
        name="some_pipeline",
        node_defs=[
            SolidDefinition(
                name="int_config_op",
                config_schema=Field(Int, is_required=False),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    assert env_type.fields["ops"].is_required is False

    solids_type = env_type.fields["ops"].config_type

    assert solids_type.fields["int_config_op"].is_required is False

    env_obj = ResolvedRunConfig.build(job_def, {})

    assert env_obj.solids["int_config_op"].config is None


def test_optional_solid_with_required_scalar_config():
    def _assert_config_none(context, value):
        assert context.op_config is value

    job_def = GraphDefinition(
        name="some_pipeline",
        node_defs=[
            SolidDefinition(
                name="int_config_op",
                config_schema=Int,
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    assert env_type.fields["ops"].is_required is True

    solids_type = env_type.fields["ops"].config_type

    assert solids_type.fields["int_config_op"].is_required is True

    int_config_solid_type = solids_type.fields["int_config_op"].config_type

    assert_has_fields(int_config_solid_type, "config")

    int_config_solid_config_field = int_config_solid_type.fields["config"]

    assert int_config_solid_config_field.is_required is True

    job_def.execute_in_process({"ops": {"int_config_op": {"config": 234}}})


def test_required_solid_with_required_subfield():
    job_def = GraphDefinition(
        name="some_pipeline",
        node_defs=[
            SolidDefinition(
                name="int_config_op",
                config_schema={"required_field": String},
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    assert env_type.fields["ops"].is_required is True
    assert env_type.fields["ops"].config_type

    solids_type = env_type.fields["ops"].config_type
    assert solids_type.fields["int_config_op"].is_required is True
    int_config_solid_type = solids_type.fields["int_config_op"].config_type
    assert int_config_solid_type.fields["config"].is_required is True

    assert env_type.fields["execution"].is_required is False

    env_obj = ResolvedRunConfig.build(
        job_def,
        {"ops": {"int_config_op": {"config": {"required_field": "foobar"}}}},
    )

    assert env_obj.solids["int_config_op"].config["required_field"] == "foobar"

    res = process_config(env_type, {"ops": {}})
    assert not res.success

    res = process_config(env_type, {})
    assert not res.success


def test_optional_solid_with_optional_subfield():
    job_def = GraphDefinition(
        name="some_pipeline",
        node_defs=[
            SolidDefinition(
                name="int_config_op",
                config_schema=Field(
                    {"optional_field": Field(String, is_required=False)},
                    is_required=False,
                ),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False
    assert env_type.fields["execution"].is_required is False


def nested_field(config_type, *field_names):
    assert field_names

    field = config_type.fields[field_names[0]]

    for field_name in field_names[1:]:
        field = field.config_type.fields[field_name]

    return field


def test_required_resource_with_required_subfield():
    @op(required_resource_keys={"with_required"})
    def needs_resource(_):
        pass

    job_def = GraphDefinition(name="some_pipeline", node_defs=[needs_resource],).to_job(
        resource_defs={
            "with_required": ResourceDefinition(
                resource_fn=lambda _: None,
                config_schema={"required_field": String},
            )
        }
    )

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False
    assert env_type.fields["execution"].is_required is False
    assert env_type.fields["resources"].is_required
    assert nested_field(env_type, "resources", "with_required").is_required
    assert nested_field(env_type, "resources", "with_required", "config").is_required
    assert nested_field(
        env_type, "resources", "with_required", "config", "required_field"
    ).is_required


def test_all_optional_field_on_single_resource():
    job_def = GraphDefinition(name="some_pipeline", node_defs=[],).to_job(
        resource_defs={
            "with_optional": ResourceDefinition(
                resource_fn=lambda _: None,
                config_schema={"optional_field": Field(String, is_required=False)},
            )
        }
    )

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False
    assert env_type.fields["execution"].is_required is False
    assert env_type.fields["resources"].is_required is False
    assert nested_field(env_type, "resources", "with_optional").is_required is False
    assert nested_field(env_type, "resources", "with_optional", "config").is_required is False
    assert (
        nested_field(env_type, "resources", "with_optional", "config", "optional_field").is_required
        is False
    )


def test_optional_and_required_context():
    @op(required_resource_keys={"required_resource"})
    def needs_resource(_):
        pass

    job_def = GraphDefinition(name="some_pipeline", node_defs=[needs_resource],).to_job(
        resource_defs={
            "optional_resource": ResourceDefinition(
                lambda _: None,
                config_schema={"optional_field": Field(String, is_required=False)},
            ),
            "required_resource": ResourceDefinition(
                lambda _: None,
                config_schema={"required_field": String},
            ),
        },
    )

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False

    assert env_type.fields["execution"].is_required is False

    assert nested_field(env_type, "resources").is_required
    assert nested_field(env_type, "resources", "optional_resource").is_required is False
    assert nested_field(env_type, "resources", "optional_resource", "config").is_required is False
    assert (
        nested_field(
            env_type, "resources", "optional_resource", "config", "optional_field"
        ).is_required
        is False
    )

    assert nested_field(env_type, "resources", "required_resource").is_required
    assert nested_field(env_type, "resources", "required_resource", "config").is_required
    assert nested_field(
        env_type, "resources", "required_resource", "config", "required_field"
    ).is_required

    env_obj = ResolvedRunConfig.build(
        job_def,
        {"resources": {"required_resource": {"config": {"required_field": "foo"}}}},
    )

    assert env_obj.resources == {
        "required_resource": ResourceConfig({"required_field": "foo"}),
        "io_manager": ResourceConfig(None),
    }


def test_required_inputs():
    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_one(num):
        return num + 1

    job_def = GraphDefinition(
        name="required_int_input",
        node_defs=[add_one],
        dependencies={
            NodeInvocation("add_one", "first_add"): {},
            NodeInvocation("add_one", "second_add"): {"num": DependencyDefinition("first_add")},
        },
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    solids_type = env_type.fields["ops"].config_type

    first_add_fields = solids_type.fields["first_add"].config_type.fields

    assert "inputs" in first_add_fields

    inputs_field = first_add_fields["inputs"]

    assert inputs_field.is_required

    assert inputs_field.config_type.fields["num"].is_required

    # second_add has a dependency so the input is not available
    assert "inputs" not in solids_type.fields["second_add"].config_type.fields


def test_mix_required_inputs():
    @op(
        ins={"left": In(Int), "right": In(Int)},
        out=Out(Int),
    )
    def add_numbers(left, right):
        return left + right

    @op
    def return_three():
        return 3

    job_def = GraphDefinition(
        name="mixed_required_inputs",
        node_defs=[add_numbers, return_three],
        dependencies={"add_numbers": {"right": DependencyDefinition("return_three")}},
    ).to_job()

    env_type = create_run_config_schema_type(job_def)
    solids_type = env_type.fields["ops"].config_type
    add_numbers_type = solids_type.fields["add_numbers"].config_type
    inputs_fields_dict = add_numbers_type.fields["inputs"].config_type.fields

    assert "left" in inputs_fields_dict
    assert not "right" in inputs_fields_dict


def test_directly_init_environment_config():
    ResolvedRunConfig()

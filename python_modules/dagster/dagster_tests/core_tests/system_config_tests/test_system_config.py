import re

from dagster import (
    Any,
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    OutputDefinition,
    PipelineDefinition,
    ResourceDefinition,
    Shape,
    SolidDefinition,
    SolidInvocation,
    String,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.config.config_type import ConfigTypeKind
from dagster.config.validate import process_config
from dagster.core.definitions import create_environment_type, create_run_config_schema
from dagster.core.definitions.environment_configs import (
    EnvironmentClassCreationData,
    define_solid_dictionary_cls,
)
from dagster.core.system_config.objects import EnvironmentConfig, SolidConfig
from dagster.loggers import default_loggers


def create_creation_data(pipeline_def):
    return EnvironmentClassCreationData(
        pipeline_def.name,
        pipeline_def.solids,
        pipeline_def.dependency_structure,
        pipeline_def.mode_definition,
        logger_defs=default_loggers(),
        ignored_solids=[],
    )


def test_all_types_provided():
    pipeline_def = PipelineDefinition(
        name="pipeline",
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                name="SomeMode",
                resource_defs={
                    "some_resource": ResourceDefinition(
                        lambda _: None,
                        config_schema={
                            "with_default_int": Field(Int, is_required=False, default_value=23434)
                        },
                    )
                },
            )
        ],
    )

    run_config_schema = create_run_config_schema(pipeline_def)

    all_types = list(run_config_schema.all_config_types())

    matching_types = [
        tt
        for tt in all_types
        if tt.kind == ConfigTypeKind.STRICT_SHAPE and "with_default_int" in tt.fields.keys()
    ]
    assert len(matching_types) == 1


def test_provided_default_on_resources_config():
    @solid(name="some_solid", input_defs=[], output_defs=[])
    def some_solid(_):
        return None

    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="some_mode",
                resource_defs={
                    "some_resource": ResourceDefinition(
                        resource_fn=lambda _: None,
                        config_schema={
                            "with_default_int": Field(Int, is_required=False, default_value=23434)
                        },
                    )
                },
            )
        ]
    )
    def pipeline_def():
        some_solid()

    env_type = create_environment_type(pipeline_def)
    some_resource_field = env_type.fields["resources"].config_type.fields["some_resource"]
    assert some_resource_field.is_required is False

    some_resource_config_field = some_resource_field.config_type.fields["config"]
    assert some_resource_config_field.is_required is False
    assert some_resource_config_field.default_value == {"with_default_int": 23434}

    assert some_resource_field.default_value == {"config": {"with_default_int": 23434}}

    value = EnvironmentConfig.build(pipeline_def, {})
    assert value.resources == {
        "some_resource": {"config": {"with_default_int": 23434}},
        "io_manager": {},
    }


def test_default_environment():
    @solid(name="some_solid", input_defs=[], output_defs=[])
    def some_solid(_):
        return None

    @pipeline
    def pipeline_def():
        some_solid()

    assert EnvironmentConfig.build(pipeline_def, {})


def test_solid_config():
    solid_config_type = Shape({"config": Field(Int)})
    solid_inst = process_config(solid_config_type, {"config": 1})
    assert solid_inst.value["config"] == 1


def test_solid_dictionary_type():
    pipeline_def = define_test_solids_config_pipeline()

    env_obj = EnvironmentConfig.build(
        pipeline_def,
        {
            "solids": {"int_config_solid": {"config": 1}, "string_config_solid": {"config": "bar"}},
        },
    )

    value = env_obj.solids

    assert set(["int_config_solid", "string_config_solid"]) == set(value.keys())
    assert value == {
        "int_config_solid": SolidConfig.from_dict({"config": 1}),
        "string_config_solid": SolidConfig.from_dict({"config": "bar"}),
    }


def define_test_solids_config_pipeline():
    @solid(
        name="int_config_solid",
        config_schema=Field(Int, is_required=False),
        input_defs=[],
        output_defs=[],
    )
    def int_config_solid(_):
        return None

    @solid(
        name="string_config_solid",
        config_schema=Field(String, is_required=False),
        input_defs=[],
        output_defs=[],
    )
    def string_config_solid(_):
        return None

    @pipeline
    def pipeline_def():
        int_config_solid()
        string_config_solid()

    return pipeline_def


def assert_has_fields(dtype, *fields):
    return set(dtype.fields.keys()) == set(fields)


def test_solid_configs_defaults():
    env_type = create_environment_type(define_test_solids_config_pipeline())

    solids_field = env_type.fields["solids"]

    assert_has_fields(solids_field.config_type, "int_config_solid", "string_config_solid")

    int_solid_field = solids_field.config_type.fields["int_config_solid"]

    assert int_solid_field.is_required is False
    # TODO: this is the test case the exposes the default dodginess
    # https://github.com/dagster-io/dagster/issues/1990
    assert int_solid_field.default_provided

    assert_has_fields(int_solid_field.config_type, "config")

    int_solid_config_field = int_solid_field.config_type.fields["config"]

    assert int_solid_config_field.is_required is False
    assert not int_solid_config_field.default_provided


def test_solid_dictionary_some_no_config():
    @solid(name="int_config_solid", config_schema=Int, input_defs=[], output_defs=[])
    def int_config_solid(_):
        return None

    @solid(name="no_config_solid", input_defs=[], output_defs=[])
    def no_config_solid(_):
        return None

    @pipeline
    def pipeline_def():
        int_config_solid()
        no_config_solid()

    env = EnvironmentConfig.build(pipeline_def, {"solids": {"int_config_solid": {"config": 1}}})

    assert {"int_config_solid", "no_config_solid"} == set(env.solids.keys())
    assert env.solids == {
        "int_config_solid": SolidConfig.from_dict({"config": 1}),
        "no_config_solid": SolidConfig.from_dict({}),
    }


def test_whole_environment():
    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        mode_defs=[
            ModeDefinition(
                name="test_mode",
                resource_defs={
                    "test_resource": ResourceDefinition(
                        resource_fn=lambda _: None, config_schema=Any
                    )
                },
            )
        ],
        solid_defs=[
            SolidDefinition(
                name="int_config_solid",
                config_schema=Int,
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *args: None,
            ),
            SolidDefinition(
                name="no_config_solid", input_defs=[], output_defs=[], compute_fn=lambda *args: None
            ),
        ],
    )

    env = EnvironmentConfig.build(
        pipeline_def,
        {
            "resources": {"test_resource": {"config": 1}},
            "solids": {"int_config_solid": {"config": 123}},
        },
    )

    assert isinstance(env, EnvironmentConfig)
    assert env.solids == {
        "int_config_solid": SolidConfig.from_dict({"config": 123}),
        "no_config_solid": SolidConfig.from_dict({}),
    }
    assert env.resources == {"test_resource": {"config": 1}, "io_manager": {}}


def test_solid_config_error():
    pipeline_def = define_test_solids_config_pipeline()
    solid_dict_type = define_solid_dictionary_cls(
        solids=pipeline_def.solids,
        ignored_solids=None,
        dependency_structure=pipeline_def.dependency_structure,
        parent_handle=None,
        resource_defs={},
    )

    int_solid_config_type = solid_dict_type.fields["int_config_solid"].config_type

    res = process_config(int_solid_config_type, {"notconfig": 1})
    assert not res.success
    assert re.match('Received unexpected config entry "notconfig"', res.errors[0].message)

    res = process_config(int_solid_config_type, 1)
    assert not res.success


def test_optional_solid_with_no_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[
            SolidDefinition(
                name="int_config_solid",
                config_schema=Int,
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            ),
            SolidDefinition(
                name="no_config_solid",
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, None),
            ),
        ],
    )

    assert execute_pipeline(pipeline_def, {"solids": {"int_config_solid": {"config": 234}}}).success


def test_optional_solid_with_optional_scalar_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[
            SolidDefinition(
                name="int_config_solid",
                config_schema=Field(Int, is_required=False),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields["solids"].is_required is False

    solids_type = env_type.fields["solids"].config_type

    assert solids_type.fields["int_config_solid"].is_required is False

    env_obj = EnvironmentConfig.build(pipeline_def, {})

    assert env_obj.solids["int_config_solid"].config is None


def test_optional_solid_with_required_scalar_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[
            SolidDefinition(
                name="int_config_solid",
                config_schema=Int,
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields["solids"].is_required is True

    solids_type = env_type.fields["solids"].config_type

    assert solids_type.fields["int_config_solid"].is_required is True

    int_config_solid_type = solids_type.fields["int_config_solid"].config_type

    assert_has_fields(int_config_solid_type, "config")

    int_config_solid_config_field = int_config_solid_type.fields["config"]

    assert int_config_solid_config_field.is_required is True

    execute_pipeline(pipeline_def, {"solids": {"int_config_solid": {"config": 234}}})


def test_required_solid_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[
            SolidDefinition(
                name="int_config_solid",
                config_schema={"required_field": String},
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields["solids"].is_required is True
    assert env_type.fields["solids"].config_type

    solids_type = env_type.fields["solids"].config_type
    assert solids_type.fields["int_config_solid"].is_required is True
    int_config_solid_type = solids_type.fields["int_config_solid"].config_type
    assert int_config_solid_type.fields["config"].is_required is True

    assert env_type.fields["execution"].is_required is False

    env_obj = EnvironmentConfig.build(
        pipeline_def,
        {"solids": {"int_config_solid": {"config": {"required_field": "foobar"}}}},
    )

    assert env_obj.solids["int_config_solid"].config["required_field"] == "foobar"

    res = process_config(env_type, {"solids": {}})
    assert not res.success

    res = process_config(env_type, {})
    assert not res.success


def test_optional_solid_with_optional_subfield():
    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[
            SolidDefinition(
                name="int_config_solid",
                config_schema=Field(
                    {"optional_field": Field(String, is_required=False)}, is_required=False
                ),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields["solids"].is_required is False
    assert env_type.fields["execution"].is_required is False


def nested_field(config_type, *field_names):
    assert field_names

    field = config_type.fields[field_names[0]]

    for field_name in field_names[1:]:
        field = field.config_type.fields[field_name]

    return field


def test_required_resource_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "with_required": ResourceDefinition(
                        resource_fn=lambda _: None,
                        config_schema={"required_field": String},
                    )
                }
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields["solids"].is_required is False
    assert env_type.fields["execution"].is_required is False
    assert env_type.fields["resources"].is_required
    assert nested_field(env_type, "resources", "with_required").is_required
    assert nested_field(env_type, "resources", "with_required", "config").is_required
    assert nested_field(
        env_type, "resources", "with_required", "config", "required_field"
    ).is_required


def test_all_optional_field_on_single_resource():
    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "with_optional": ResourceDefinition(
                        resource_fn=lambda _: None,
                        config_schema={"optional_field": Field(String, is_required=False)},
                    )
                }
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields["solids"].is_required is False
    assert env_type.fields["execution"].is_required is False
    assert env_type.fields["resources"].is_required is False
    assert nested_field(env_type, "resources", "with_optional").is_required is False
    assert nested_field(env_type, "resources", "with_optional", "config").is_required is False
    assert (
        nested_field(env_type, "resources", "with_optional", "config", "optional_field").is_required
        is False
    )


def test_optional_and_required_context():
    pipeline_def = PipelineDefinition(
        name="some_pipeline",
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                name="mixed",
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
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields["solids"].is_required is False

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

    env_obj = EnvironmentConfig.build(
        pipeline_def,
        {"resources": {"required_resource": {"config": {"required_field": "foo"}}}},
    )

    assert env_obj.resources == {
        "optional_resource": {"config": {}},
        "required_resource": {"config": {"required_field": "foo"}},
        "io_manager": {},
    }


def test_required_inputs():
    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name="required_int_input",
        solid_defs=[add_one],
        dependencies={
            SolidInvocation("add_one", "first_add"): {},
            SolidInvocation("add_one", "second_add"): {"num": DependencyDefinition("first_add")},
        },
    )

    env_type = create_environment_type(pipeline_def)

    solids_type = env_type.fields["solids"].config_type

    first_add_fields = solids_type.fields["first_add"].config_type.fields

    assert "inputs" in first_add_fields

    inputs_field = first_add_fields["inputs"]

    assert inputs_field.is_required

    assert inputs_field.config_type.fields["num"].is_required

    # second_add has a dependency so the input is not available
    assert "inputs" not in solids_type.fields["second_add"].config_type.fields


def test_mix_required_inputs():
    @lambda_solid(
        input_defs=[InputDefinition("left", Int), InputDefinition("right", Int)],
        output_def=OutputDefinition(Int),
    )
    def add_numbers(left, right):
        return left + right

    @lambda_solid
    def return_three():
        return 3

    pipeline_def = PipelineDefinition(
        name="mixed_required_inputs",
        solid_defs=[add_numbers, return_three],
        dependencies={"add_numbers": {"right": DependencyDefinition("return_three")}},
    )

    env_type = create_environment_type(pipeline_def)
    solids_type = env_type.fields["solids"].config_type
    add_numbers_type = solids_type.fields["add_numbers"].config_type
    inputs_fields_dict = add_numbers_type.fields["inputs"].config_type.fields

    assert "left" in inputs_fields_dict
    assert not "right" in inputs_fields_dict


def test_files_default_config():
    pipeline_def = PipelineDefinition(name="pipeline", solid_defs=[])

    env_type = create_environment_type(pipeline_def)
    assert "storage" in env_type.fields

    config_value = process_config(env_type, {})
    assert config_value.success

    assert "storage" not in config_value


def test_storage_in_memory_config():
    pipeline_def = PipelineDefinition(name="pipeline", solid_defs=[])

    env_type = create_environment_type(pipeline_def)
    assert "storage" in env_type.fields

    config_value = process_config(env_type, {"intermediate_storage": {"in_memory": {}}})
    assert config_value.success

    assert config_value.value["intermediate_storage"] == {"in_memory": {}}


def test_directly_init_environment_config():
    EnvironmentConfig()

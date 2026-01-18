import re
from typing import cast

import dagster as dg
from dagster import Any, Int
from dagster._config import ConfigTypeKind, process_config
from dagster._config.config_type import ConfigType
from dagster._config.field_utils import Permissive, Shape
from dagster._core.definitions import create_run_config_schema
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.run_config import RunConfigSchemaCreationData, define_node_config
from dagster._core.system_config.objects import OpConfig, ResolvedRunConfig, ResourceConfig


def create_creation_data(job_def):
    return RunConfigSchemaCreationData(  # pyright: ignore[reportCallIssue]
        job_def.name,
        job_def.nodes,
        job_def.dependency_structure,
        logger_defs=dg.default_loggers(),
        ignored_nodes=[],
        required_resources=set(),
        direct_inputs=job_def._input_values,  # noqa [SLF001]
        asset_layer=job_def.asset_layer,
    )


def create_run_config_schema_type(job_def: JobDefinition) -> ConfigType:
    return job_def.run_config_schema.config_type


def test_all_types_provided():
    job_def = dg.GraphDefinition(
        name="pipeline",
        node_defs=[],
    ).to_job(
        resource_defs={
            "some_resource": dg.ResourceDefinition(
                lambda _: None,
                config_schema={
                    "with_default_int": dg.Field(dg.Int, is_required=False, default_value=23434)
                },
            )
        },
    )

    run_config_schema = create_run_config_schema(job_def)

    all_types = list(run_config_schema.all_config_types())

    matching_types = [
        tt
        for tt in all_types
        if tt.kind == ConfigTypeKind.STRICT_SHAPE and "with_default_int" in tt.fields.keys()  # pyright: ignore[reportAttributeAccessIssue]
    ]
    assert len(matching_types) == 1


def test_provided_default_on_resources_config():
    @dg.op(
        name="some_op",
        ins={},
        out={},
        required_resource_keys={"some_resource"},
    )
    def some_op(_):
        return None

    @dg.job(
        resource_defs={
            "some_resource": dg.ResourceDefinition(
                resource_fn=lambda _: None,
                config_schema={
                    "with_default_int": dg.Field(dg.Int, is_required=False, default_value=23434)
                },
            )
        }
    )
    def job_def():
        some_op()

    env_type = create_run_config_schema_type(job_def)
    some_resource_field = env_type.fields["resources"].config_type.fields["some_resource"]  # pyright: ignore[reportAttributeAccessIssue]
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
    @dg.op(name="some_op", ins={}, out={})
    def some_op(_):
        return None

    @dg.job
    def job_def():
        some_op()

    assert ResolvedRunConfig.build(job_def, {})


def test_op_config():
    solid_config_type = dg.Shape({"config": dg.Field(dg.Int)})
    solid_inst = process_config(solid_config_type, {"config": 1})
    assert solid_inst.value["config"] == 1  # pyright: ignore[reportOptionalSubscript]


def test_op_dictionary_type():
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

    value = env_obj.ops

    assert set(["int_config_op", "string_config_op"]) == set(value.keys())
    assert value == {
        "int_config_op": OpConfig.from_dict({"config": 1}),
        "string_config_op": OpConfig.from_dict({"config": "bar"}),
    }


def define_test_solids_config_pipeline():
    @dg.op(
        name="int_config_op",
        config_schema=dg.Field(dg.Int, is_required=False),
        ins={},
        out={},
    )
    def int_config_op(_):
        return None

    @dg.op(
        name="string_config_op",
        config_schema=dg.Field(dg.String, is_required=False),
        ins={},
        out={},
    )
    def string_config_op(_):
        return None

    @dg.job
    def job_def():
        int_config_op()
        string_config_op()

    return job_def


def assert_has_fields(dtype, *fields):
    return set(dtype.fields.keys()) == set(fields)


def test_op_configs_defaults():
    env_type = create_run_config_schema_type(define_test_solids_config_pipeline())

    solids_field = env_type.fields["ops"]  # pyright: ignore[reportAttributeAccessIssue]

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


def test_op_dictionary_some_no_config():
    @dg.op(name="int_config_op", config_schema=Int, ins={}, out={})
    def int_config_op(_):
        return None

    @dg.op(name="no_config_op", ins={}, out={})
    def no_config_op(_):
        return None

    @dg.job
    def job_def():
        int_config_op()
        no_config_op()

    env = ResolvedRunConfig.build(job_def, {"ops": {"int_config_op": {"config": 1}}})

    assert {"int_config_op", "no_config_op"} == set(env.ops.keys())
    assert env.ops == {
        "int_config_op": OpConfig.from_dict({"config": 1}),
        "no_config_op": OpConfig.from_dict({}),
    }


def test_whole_environment():
    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[
            dg.OpDefinition(
                name="int_config_op",
                config_schema=Int,
                ins={},
                outs={"result": dg.Out()},
                required_resource_keys={"test_resource"},
                compute_fn=lambda *args: None,
            ),
            dg.OpDefinition(
                name="no_config_op",
                ins={},
                outs={},
                compute_fn=lambda *args: None,
            ),
        ],
    ).to_job(
        resource_defs={
            "test_resource": dg.ResourceDefinition(resource_fn=lambda _: None, config_schema=Any)  # pyright: ignore[reportArgumentType]
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
    assert env.ops == {
        "int_config_op": OpConfig.from_dict({"config": 123}),
        "no_config_op": OpConfig.from_dict({}),
    }
    assert env.resources == {
        "test_resource": ResourceConfig(1),
        "io_manager": ResourceConfig(None),
    }


def test_op_config_error():
    job_def = define_test_solids_config_pipeline()
    solid_dict_type = define_node_config(
        nodes=job_def.nodes,
        ignored_nodes=None,
        dependency_structure=job_def.dependency_structure,
        parent_handle=None,
        resource_defs={},
        asset_layer=job_def.asset_layer,
        input_assets={},
    )

    int_solid_config_type = solid_dict_type.fields["int_config_op"].config_type

    res = process_config(int_solid_config_type, {"notconfig": 1})
    assert not res.success
    assert re.match('Received unexpected config entry "notconfig"', res.errors[0].message)  # pyright: ignore[reportOptionalSubscript]

    res = process_config(int_solid_config_type, 1)  # pyright: ignore[reportArgumentType]
    assert not res.success


def test_optional_op_with_no_config():
    def _assert_config_none(context, value):
        assert context.op_config is value

    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[
            dg.OpDefinition(
                name="int_config_op",
                config_schema=Int,
                ins={},
                outs={},
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            ),
            dg.OpDefinition(
                name="no_config_op",
                ins={},
                outs={},
                compute_fn=lambda context, _inputs: _assert_config_none(context, None),
            ),
        ],
    ).to_job()

    assert job_def.execute_in_process({"ops": {"int_config_op": {"config": 234}}}).success


def test_optional_op_with_optional_scalar_config():
    def _assert_config_none(context, value):
        assert context.op_config is value

    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[
            dg.OpDefinition(
                name="int_config_op",
                config_schema=dg.Field(dg.Int, is_required=False),
                ins={},
                outs={},
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    assert env_type.fields["ops"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]

    solids_type = env_type.fields["ops"].config_type  # pyright: ignore[reportAttributeAccessIssue]

    assert solids_type.fields["int_config_op"].is_required is False

    env_obj = ResolvedRunConfig.build(job_def, {})

    assert env_obj.ops["int_config_op"].config is None


def test_optional_op_with_required_scalar_config():
    def _assert_config_none(context, value):
        assert context.op_config is value

    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[
            dg.OpDefinition(
                name="int_config_op",
                config_schema=Int,
                ins={},
                outs={},
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    assert env_type.fields["ops"].is_required is True  # pyright: ignore[reportAttributeAccessIssue]

    solids_type = env_type.fields["ops"].config_type  # pyright: ignore[reportAttributeAccessIssue]

    assert solids_type.fields["int_config_op"].is_required is True

    int_config_solid_type = solids_type.fields["int_config_op"].config_type

    assert_has_fields(int_config_solid_type, "config")

    int_config_solid_config_field = int_config_solid_type.fields["config"]

    assert int_config_solid_config_field.is_required is True

    job_def.execute_in_process({"ops": {"int_config_op": {"config": 234}}})


def test_required_op_with_required_subfield():
    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[
            dg.OpDefinition(
                name="int_config_op",
                config_schema={"required_field": dg.String},
                ins={},
                outs={},
                compute_fn=lambda *_args: None,
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    assert env_type.fields["ops"].is_required is True  # pyright: ignore[reportAttributeAccessIssue]
    assert env_type.fields["ops"].config_type  # pyright: ignore[reportAttributeAccessIssue]

    solids_type = env_type.fields["ops"].config_type  # pyright: ignore[reportAttributeAccessIssue]
    assert solids_type.fields["int_config_op"].is_required is True
    int_config_solid_type = solids_type.fields["int_config_op"].config_type
    assert int_config_solid_type.fields["config"].is_required is True

    assert env_type.fields["execution"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]

    env_obj = ResolvedRunConfig.build(
        job_def,
        {"ops": {"int_config_op": {"config": {"required_field": "foobar"}}}},
    )

    assert env_obj.ops["int_config_op"].config["required_field"] == "foobar"  # pyright: ignore[reportIndexIssue]

    res = process_config(env_type, {"ops": {}})
    assert not res.success

    res = process_config(env_type, {})
    assert not res.success


def test_implicit_asset_job_subset_config():
    class MyConnectionResource(dg.ConfigurableResource):
        username: str

    class MyOtherResource(dg.ConfigurableResource):
        groupname: str

    @dg.asset(config_schema={"foo": int})
    def asset(my_conn: MyConnectionResource):
        return 1

    @dg.asset(config_schema={"bar": int})
    def asset2():
        return 2

    @dg.asset
    def asset3(my_other_conn: MyOtherResource):
        return 3

    @dg.asset
    def asset_without_config():
        return 3

    defs = dg.Definitions(
        assets=[asset, asset2, asset3, asset_without_config],
        jobs=[
            dg.define_asset_job(
                "explicit_asset_job", selection=["asset", "asset2", "asset_without_config"]
            )
        ],
        resources={
            "my_conn": MyConnectionResource(username="my_user"),
            "my_other_conn": MyOtherResource(groupname="my_group"),
        },
    )

    explicit_asset_job = defs.resolve_job_def("explicit_asset_job")
    explicit_asset_job_subset = explicit_asset_job.get_subset(
        asset_selection={dg.AssetKey(["asset"])}
    )

    implicit_asset_job_subset = defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_selection={dg.AssetKey(["asset"]), dg.AssetKey(["asset2"])}
    )

    # implicit asset job subset only reference the specific assets in the subset
    implicit_subset_env_type = create_run_config_schema_type(implicit_asset_job_subset)
    assert isinstance(implicit_subset_env_type, Shape)
    assert isinstance(implicit_subset_env_type.fields["ops"].config_type, Permissive)
    assert isinstance(implicit_subset_env_type.fields["resources"].config_type, Permissive)
    ops_permissive = cast("Permissive", implicit_subset_env_type.fields["ops"].config_type)
    assert ops_permissive.fields.keys() == {
        "asset",
        "asset2",
    }

    resources_permissive = cast(
        "Permissive", implicit_subset_env_type.fields["resources"].config_type
    )
    assert resources_permissive.fields.keys() == {
        "io_manager",
        "my_conn",
    }

    # despite having an asset_selection of just one asset, the subset job still includes the other assets
    # in the job are not in the selection, since the job is an explicitly defined subset
    explicit_subset_env_type = create_run_config_schema_type(explicit_asset_job_subset)
    assert isinstance(explicit_subset_env_type, Shape)
    assert isinstance(explicit_subset_env_type.fields["ops"].config_type, Shape)
    assert isinstance(explicit_subset_env_type.fields["resources"].config_type, Shape)

    ops_shape = cast("Shape", explicit_subset_env_type.fields["ops"].config_type)

    assert ops_shape.fields.keys() == {
        "asset",
        "asset2",
        "asset_without_config",
    }

    resources_shape = cast("Shape", explicit_subset_env_type.fields["resources"].config_type)

    assert resources_shape.fields.keys() == {
        "io_manager",
        "my_conn",
        "my_other_conn",
    }


def test_optional_op_with_optional_subfield():
    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[
            dg.OpDefinition(
                name="int_config_op",
                config_schema=dg.Field(
                    {"optional_field": dg.Field(dg.String, is_required=False)},
                    is_required=False,
                ),
                ins={},
                outs={},
                compute_fn=lambda *_args: None,
            )
        ],
    ).to_job()

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]
    assert env_type.fields["execution"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]


def nested_field(config_type, *field_names):
    assert field_names

    field = config_type.fields[field_names[0]]

    for field_name in field_names[1:]:
        field = field.config_type.fields[field_name]

    return field


def test_required_resource_with_required_subfield():
    @dg.op(required_resource_keys={"with_required"})
    def needs_resource(_):
        pass

    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[needs_resource],
    ).to_job(
        resource_defs={
            "with_required": dg.ResourceDefinition(
                resource_fn=lambda _: None,
                config_schema={"required_field": dg.String},
            )
        }
    )

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]
    assert env_type.fields["execution"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]
    assert env_type.fields["resources"].is_required  # pyright: ignore[reportAttributeAccessIssue]
    assert nested_field(env_type, "resources", "with_required").is_required
    assert nested_field(env_type, "resources", "with_required", "config").is_required
    assert nested_field(
        env_type, "resources", "with_required", "config", "required_field"
    ).is_required


def test_all_optional_field_on_single_resource():
    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[],
    ).to_job(
        resource_defs={
            "with_optional": dg.ResourceDefinition(
                resource_fn=lambda _: None,
                config_schema={"optional_field": dg.Field(dg.String, is_required=False)},
            )
        }
    )

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]
    assert env_type.fields["execution"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]
    assert env_type.fields["resources"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]
    assert nested_field(env_type, "resources", "with_optional").is_required is False
    assert nested_field(env_type, "resources", "with_optional", "config").is_required is False
    assert (
        nested_field(env_type, "resources", "with_optional", "config", "optional_field").is_required
        is False
    )


def test_optional_and_required_context():
    @dg.op(required_resource_keys={"required_resource"})
    def needs_resource(_):
        pass

    job_def = dg.GraphDefinition(
        name="some_pipeline",
        node_defs=[needs_resource],
    ).to_job(
        resource_defs={
            "optional_resource": dg.ResourceDefinition(
                lambda _: None,
                config_schema={"optional_field": dg.Field(dg.String, is_required=False)},
            ),
            "required_resource": dg.ResourceDefinition(
                lambda _: None,
                config_schema={"required_field": dg.String},
            ),
        },
    )

    env_type = create_run_config_schema_type(job_def)
    assert env_type.fields["ops"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]

    assert env_type.fields["execution"].is_required is False  # pyright: ignore[reportAttributeAccessIssue]

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
    @dg.op(ins={"num": dg.In(dg.Int)}, out=dg.Out(dg.Int))
    def add_one(num):
        return num + 1

    job_def = dg.GraphDefinition(
        name="required_int_input",
        node_defs=[add_one],
        dependencies={
            dg.NodeInvocation("add_one", "first_add"): {},
            dg.NodeInvocation("add_one", "second_add"): {
                "num": dg.DependencyDefinition("first_add")
            },
        },
    ).to_job()

    env_type = create_run_config_schema_type(job_def)

    solids_type = env_type.fields["ops"].config_type  # pyright: ignore[reportAttributeAccessIssue]

    first_add_fields = solids_type.fields["first_add"].config_type.fields

    assert "inputs" in first_add_fields

    inputs_field = first_add_fields["inputs"]

    assert inputs_field.is_required

    assert inputs_field.config_type.fields["num"].is_required

    # second_add has a dependency so the input is not available
    assert "inputs" not in solids_type.fields["second_add"].config_type.fields


def test_mix_required_inputs():
    @dg.op(
        ins={"left": dg.In(dg.Int), "right": dg.In(dg.Int)},
        out=dg.Out(dg.Int),
    )
    def add_numbers(left, right):
        return left + right

    @dg.op
    def return_three():
        return 3

    job_def = dg.GraphDefinition(
        name="mixed_required_inputs",
        node_defs=[add_numbers, return_three],
        dependencies={"add_numbers": {"right": dg.DependencyDefinition("return_three")}},
    ).to_job()

    env_type = create_run_config_schema_type(job_def)
    solids_type = env_type.fields["ops"].config_type  # pyright: ignore[reportAttributeAccessIssue]
    add_numbers_type = solids_type.fields["add_numbers"].config_type
    inputs_fields_dict = add_numbers_type.fields["inputs"].config_type.fields

    assert "left" in inputs_fields_dict
    assert "right" not in inputs_fields_dict


def test_directly_init_environment_config():
    ResolvedRunConfig()

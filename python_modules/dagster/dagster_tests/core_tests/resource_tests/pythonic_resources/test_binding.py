from typing import cast

import pytest
from dagster import (
    BindResourcesToJobs,
    Config,
    ConfigurableIOManager,
    ConfigurableResource,
    Definitions,
    FilesystemIOManager,
    JobDefinition,
    RunRequest,
    ScheduleDefinition,
    asset,
    job,
    op,
    repository,
    resource,
    sensor,
)
from dagster._core.definitions.repository_definition.repository_data_builder import (
    build_caching_repository_data_from_dict,
)
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
)


def test_bind_resource_to_job_at_defn_time_err() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    # Validate that jobs without bound resources error at repository construction time
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        build_caching_repository_data_from_dict({"jobs": {"hello_world_job": hello_world_job}})

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):

        @repository
        def my_repo():
            return [hello_world_job]

    # Validate that this also happens with Definitions
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        Definitions(
            jobs=[hello_world_job],
        )


def test_bind_resource_to_job_at_defn_time() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    # Bind the resource to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "writer": WriterResource(prefix=""),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["msg: hello, world!"]


def test_bind_resource_to_job_at_defn_time_bind_resources_to_jobs() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    # BindResourcesToJobs is a no-op now
    defs = Definitions(
        jobs=BindResourcesToJobs([hello_world_job]),
        resources={
            "writer": WriterResource(prefix=""),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    # BindResourcesToJobs is a no-op now
    defs = Definitions(
        jobs=BindResourcesToJobs([hello_world_job]),
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["msg: hello, world!"]


def test_bind_resource_to_job_with_job_config() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    class OpConfig(Config):
        message: str = "hello, world!"

    @op
    def hello_world_op(writer: WriterResource, config: OpConfig):
        writer.output(config.message)

    @job(config={})
    def hello_world_job() -> None:
        hello_world_op()

    @job(config={"ops": {"hello_world_op": {"config": {"message": "hello, earth!"}}}})
    def hello_earth_job() -> None:
        hello_world_op()

    defs = Definitions(
        jobs=[hello_world_job, hello_earth_job],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["msg: hello, world!"]
    out_txt.clear()

    assert defs.get_job_def("hello_earth_job").execute_in_process().success
    assert out_txt == ["msg: hello, earth!"]

    # Validate that we correctly error
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        Definitions(
            jobs=[hello_world_job],
        )


def test_bind_resource_to_job_at_defn_time_override() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    # Binding the resource to the job at definition time should not override the resource
    @job(
        resource_defs={
            "writer": WriterResource(prefix="job says: "),
        }
    )
    def hello_world_job_with_override():
        hello_world_op()

    @job
    def hello_world_job_no_override():
        hello_world_op()

    defs = Definitions(
        jobs=[hello_world_job_with_override, hello_world_job_no_override],
        resources={
            "writer": WriterResource(prefix="definitions says: "),
        },
    )

    assert defs.get_job_def("hello_world_job_with_override").execute_in_process().success
    assert out_txt == ["job says: hello, world!"]
    out_txt.clear()

    assert defs.get_job_def("hello_world_job_no_override").execute_in_process().success
    assert out_txt == ["definitions says: hello, world!"]


@pytest.mark.parametrize("include_job_in_definitions", [True, False])
def test_bind_resource_to_instigator(include_job_in_definitions) -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    @sensor(job=hello_world_job)
    def hello_world_sensor(): ...

    hello_world_schedule = ScheduleDefinition(
        name="hello_world_schedule", cron_schedule="* * * * *", job=hello_world_job
    )

    # Bind the resource to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job] if include_job_in_definitions else [],
        schedules=[hello_world_schedule],
        sensors=[hello_world_sensor],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert (
        cast(JobDefinition, defs.get_sensor_def("hello_world_sensor").job)
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()

    assert (
        cast(JobDefinition, defs.get_schedule_def("hello_world_schedule").job)
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()


def test_bind_resource_to_instigator_by_name() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    @sensor(job_name="hello_world_job")
    def hello_world_sensor(): ...

    hello_world_schedule = ScheduleDefinition(
        name="hello_world_schedule", cron_schedule="* * * * *", job_name="hello_world_job"
    )

    # Bind the resource to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        schedules=[hello_world_schedule],
        sensors=[hello_world_sensor],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert (
        defs.get_job_def(cast(str, defs.get_sensor_def("hello_world_sensor").job_name))
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()

    assert (
        defs.get_job_def(cast(str, defs.get_schedule_def("hello_world_schedule").job_name))
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()


def test_bind_io_manager_default() -> None:
    outputs = []

    class MyIOManager(ConfigurableIOManager):
        def load_input(self, _) -> None:
            pass

        def handle_output(self, _, obj) -> None:
            outputs.append(obj)

    @op
    def hello_world_op() -> str:
        return "foo"

    @job
    def hello_world_job() -> None:
        hello_world_op()

    # Bind the I/O manager to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "io_manager": MyIOManager(),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert outputs == ["foo"]


def test_bind_io_manager_override() -> None:
    outputs = []

    class MyIOManager(ConfigurableIOManager):
        def load_input(self, _) -> None:
            pass

        def handle_output(self, _, obj) -> None:
            outputs.append(obj)

    class MyOtherIOManager(ConfigurableIOManager):
        def load_input(self, _) -> None:
            pass

        def handle_output(self, _, obj) -> None:
            pass

    @op
    def hello_world_op() -> str:
        return "foo"

    @job(resource_defs={"io_manager": MyIOManager()})
    def hello_world_job() -> None:
        hello_world_op()

    # Bind the I/O manager to the job at definition time and validate that it does
    # not take precedence over the one defined on the job
    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "io_manager": MyOtherIOManager(),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert outputs == ["foo"]


def test_bind_top_level_resource_sensor_multi_job() -> None:
    executed = {}

    class FooResource(ConfigurableResource):
        my_str: str

    @op
    def hello_world_op(foo: FooResource):
        assert foo.my_str == "foo"
        executed["yes"] = True

    @job()
    def hello_world_job():
        hello_world_op()

    @job
    def hello_world_job_2():
        hello_world_op()

    @sensor(jobs=[hello_world_job, hello_world_job_2])
    def hello_world_sensor(context):
        return RunRequest(run_key="foo")

    Definitions(
        sensors=[hello_world_sensor],
        jobs=[hello_world_job, hello_world_job_2],
        resources={
            "foo": FooResource(my_str="foo"),
        },
    )


def test_override_default_value_in_asset_config() -> None:
    class MyAssetConfig(Config):
        str_field: str = "a_default_value"

    executed = {}

    @asset
    def my_asset(config: MyAssetConfig):
        executed["yes"] = True
        return config.str_field

    defs = Definitions([my_asset])

    assert (
        defs.get_implicit_global_asset_job_def().execute_in_process().output_for_node("my_asset")
        == "a_default_value"
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(run_config={"ops": {"my_asset": {"config": {"str_field": "override"}}}})
        .output_for_node("my_asset")
        == "override"
    )


def test_override_default_value_in_ctor() -> None:
    class MyResourceWithDefault(ConfigurableResource):
        str_field: str

    executed = {}

    @asset
    def my_asset(context, my_resource: MyResourceWithDefault):
        executed["yes"] = True
        return my_resource.str_field

    defs = Definitions(
        [my_asset],
        resources={"my_resource": MyResourceWithDefault(str_field="value_set_in_ctor")},
    )

    assert (
        defs.get_implicit_global_asset_job_def().execute_in_process().output_for_node("my_asset")
        == "value_set_in_ctor"
    )

    assert executed["yes"]

    executed.clear()

    assert "yes" not in executed

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            run_config={"resources": {"my_resource": {"config": {"str_field": "overriden"}}}}
        )
        .output_for_node("my_asset")
        == "overriden"
    )

    assert executed["yes"]


def test_override_default_field_value_in_resources() -> None:
    class MyResourceWithDefault(ConfigurableResource):
        str_field: str = "value_set_in_default_field_decl"

    executed = {}

    @asset
    def my_asset(context, my_resource: MyResourceWithDefault):
        executed["yes"] = True
        return my_resource.str_field

    defs = Definitions([my_asset], resources={"my_resource": MyResourceWithDefault()})

    assert (
        defs.get_implicit_global_asset_job_def().execute_in_process().output_for_node("my_asset")
        == "value_set_in_default_field_decl"
    )

    assert executed["yes"]

    executed.clear()

    assert "yes" not in executed

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            run_config={"resources": {"my_resource": {"config": {"str_field": "overriden"}}}}
        )
        .output_for_node("my_asset")
        == "overriden"
    )

    assert executed["yes"]


def test_override_default_field_value_in_resources_using_configure_at_launch() -> None:
    class MyResourceWithDefault(ConfigurableResource):
        str_field: str = "value_set_in_default_field_decl"

    executed = {}

    @asset
    def my_asset(context, my_resource: MyResourceWithDefault):
        executed["yes"] = True
        return my_resource.str_field

    defs = Definitions(
        [my_asset], resources={"my_resource": MyResourceWithDefault.configure_at_launch()}
    )

    assert (
        defs.get_implicit_global_asset_job_def().execute_in_process().output_for_node("my_asset")
        == "value_set_in_default_field_decl"
    )

    assert executed["yes"]

    executed.clear()

    assert "yes" not in executed

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            run_config={"resources": {"my_resource": {"config": {"str_field": "overriden"}}}}
        )
        .output_for_node("my_asset")
        == "overriden"
    )

    assert executed["yes"]


class MyModuleLevelResource(ConfigurableResource):
    str_field: str


# Note that an explicit string annotation has the same effect as defining a resource in a module
# using `from __future__ import annotations`. This test will only work against a module-scoped
# resource-- this is a hard limitation of string annotations in Python as of 2023-07-06 and Python
# 3.11.
def test_bind_with_string_annotation():
    @asset
    def my_asset(context, my_resource: "MyModuleLevelResource"):
        return my_resource.str_field

    str_field_value = "foo"

    defs = Definitions(
        [my_asset], resources={"my_resource": MyModuleLevelResource(str_field=str_field_value)}
    )

    assert (
        defs.get_implicit_global_asset_job_def().execute_in_process().output_for_node("my_asset")
        == str_field_value
    )


def test_late_binding_with_resource_defs() -> None:
    queries = []

    class DummyDB:
        def execute_query(self, query):
            queries.append(query)

    @resource
    def dummy_database_resource(init_context):
        return DummyDB()

    @op(required_resource_keys={"database"})
    def op_requires_resources(context):
        context.resources.database.execute_query("foo")

    @job(resource_defs={"database": dummy_database_resource})
    def do_database_stuff():
        op_requires_resources()

    @op
    def simple_op():
        pass

    @job()
    def simple_job():
        simple_op()

    # io_manager here will be bound to both jobs
    # we need to make sure this doesn't invalidate the database resource
    defs = Definitions(
        jobs=[do_database_stuff, simple_job],
        resources={"io_manager": FilesystemIOManager()},
    )

    assert defs.get_job_def("do_database_stuff").execute_in_process().success

    assert queries == ["foo"]


def test_late_binding_with_resource_defs_override() -> None:
    queries = []

    class DummyDB:
        def execute_query(self, query):
            queries.append(query)

    @resource
    def dummy_database_resource(init_context):
        return DummyDB()

    @op(required_resource_keys={"database"})
    def op_requires_resources(context):
        context.resources.database.execute_query("foo")

    @job(resource_defs={"database": dummy_database_resource})
    def do_database_stuff():
        op_requires_resources()

    class BadDB(DummyDB):
        def execute_query(self, query):
            pass

    @resource
    def bad_database_resource(init_context):
        return BadDB()

    # io_manager here will be bound to both jobs
    # we need to make sure the bad database resource doesn't get bound, since the
    # job-level resource def should take precedence
    defs = Definitions(
        jobs=[do_database_stuff],
        resources={"io_manager": FilesystemIOManager(), "database": bad_database_resource},
    )

    assert defs.get_job_def("do_database_stuff").execute_in_process().success

    assert queries == ["foo"]

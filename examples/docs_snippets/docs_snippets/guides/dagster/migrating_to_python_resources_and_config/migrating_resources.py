from typing import Iterator

from dagster import Definitions, define_asset_job


def initial_code_base() -> Definitions:
    # begin_initial_codebase
    from dagster import (
        AssetExecutionContext,
        Definitions,
        InitResourceContext,
        asset,
        resource,
    )

    class FancyDbResource:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute(self, query: str) -> None:
            ...

    @resource(config_schema={"conn_string": str})
    def fancy_db_resource(context: InitResourceContext) -> FancyDbResource:
        return FancyDbResource(context.resource_config["conn_string"])

    @asset(required_resource_keys={"fancy_db"})
    def asset_one(context: AssetExecutionContext) -> None:
        assert context.resources.fancy_db

    @asset(required_resource_keys={"fancy_db"})
    def asset_two(context: AssetExecutionContext) -> None:
        assert context.resources.fancy_db

    defs = Definitions(
        assets=[asset_one, asset_two],
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "some_value"})
        },
    )
    # end_initial_codebase
    return defs


def convert_resource() -> Definitions:
    # begin_convert_resource
    from dagster import ConfigurableResource

    class FancyDbResource(ConfigurableResource):
        conn_string: str

        def execute(self, query: str) -> None:
            ...

    # end_convert_resource

    # begin_resource_adapter
    from dagster import InitResourceContext, resource

    @resource(config_schema=FancyDbResource.to_config_schema())
    def fancy_db_resource(context: InitResourceContext) -> FancyDbResource:
        return FancyDbResource.from_resource_context(context)

    # old-style resource API still works, but the Pythonic resource is the source of truth
    # for schema information and implementation
    defs = Definitions(
        # ...
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "some_value"})
        },
    )
    # end_resource_adapter

    return defs


def new_style_resource_on_context() -> Definitions:
    # begin_new_style_resource_on_context
    from dagster import AssetExecutionContext, ConfigurableResource, Definitions, asset

    class FancyDbResource(ConfigurableResource):
        conn_string: str

        def execute(self, query: str) -> None:
            ...

    @asset(required_resource_keys={"fancy_db"})
    def asset_one(context: AssetExecutionContext) -> None:
        # this still works because the resource is still available on the context
        assert context.resources.fancy_db

    defs = Definitions(
        assets=[asset_one],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )

    # end_new_style_resource_on_context

    return defs


def new_style_resource_on_param() -> Definitions:
    from dagster import ConfigurableResource, Definitions, OpExecutionContext, asset

    class FancyDbResource(ConfigurableResource):
        conn_string: str

        def execute(self, query: str) -> None:
            ...

    # begin_new_style_resource_on_param
    from dagster import AssetExecutionContext, asset

    @asset
    def asset_one(context: AssetExecutionContext, fancy_db: FancyDbResource) -> None:
        assert fancy_db

    # end_new_style_resource_on_param

    return Definitions(
        assets=[asset_one],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )


def old_third_party_resource() -> Definitions:
    # begin_old_third_party_resource

    # Pre-existing code that you don't want to alter
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None:
            ...

    # Alternatively could have been imported from third-party library
    # from fancy_db import FancyDbClient

    from dagster import AssetExecutionContext, InitResourceContext, asset, resource

    @resource(config_schema={"conn_string": str})
    def fancy_db_resource(context: InitResourceContext) -> FancyDbClient:
        return FancyDbClient(context.resource_config["conn_string"])

    @asset(required_resource_keys={"fancy_db"})
    def existing_asset(context: AssetExecutionContext) -> None:
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_old_third_party_resource

    defs = Definitions(
        assets=[existing_asset],
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "something"})
        },
    )

    return defs


def some_expensive_setup() -> None:
    ...


def some_expensive_teardown() -> None:
    ...


def old_resource_code_contextmanager() -> Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None:
            ...

    # begin_old_resource_code_contextmanager

    from dagster import AssetExecutionContext, InitResourceContext, asset, resource

    @resource(config_schema={"conn_string": str})
    def fancy_db_resource(context: InitResourceContext) -> Iterator[FancyDbClient]:
        some_expensive_setup()
        try:
            # the client is yielded to the assets that require it
            yield FancyDbClient(context.resource_config["conn_string"])
        finally:
            # this is only called once the asset has finished executing
            some_expensive_teardown()

    @asset(required_resource_keys={"fancy_db"})
    def asset_one(context: AssetExecutionContext) -> None:
        # some_expensive_setup() has been called, but some_expensive_teardown() has not
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_old_resource_code_contextmanager

    return Definitions(
        assets=[asset_one],
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "something"})
        },
    )


def new_resource_code_contextmanager() -> Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None:
            ...

    # begin_new_resource_code_contextmanager

    from contextlib import contextmanager

    from dagster import ConfigurableResource, asset

    class FancyDbResource(ConfigurableResource):
        conn_string: str

        @contextmanager
        def get_client(self) -> Iterator[FancyDbClient]:
            try:
                some_expensive_setup()
                yield FancyDbClient(self.conn_string)
            finally:
                some_expensive_teardown()

    @asset
    def asset_one(fancy_db: FancyDbResource) -> None:
        with fancy_db.get_client() as client:
            client.execute_query("SELECT * FROM foo")

    # end_new_resource_code_contextmanager

    return Definitions(
        assets=[asset_one],
        resources={"fancy_db": FancyDbResource(conn_string="something")},
    )


def new_third_party_resource_old_code_broken() -> Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None:
            ...

    # begin_new_third_party_resource
    from dagster import AssetExecutionContext, ConfigurableResource, asset

    class FancyDbResource(ConfigurableResource):
        conn_string: str

        def get_client(self) -> FancyDbClient:
            return FancyDbClient(self.conn_string)

    @asset
    def new_asset(fancy_db: FancyDbResource) -> None:
        client = fancy_db.get_client()
        client.execute_query("SELECT * FROM foo")

    # end_new_third_party_resource

    # begin_broken_unmigrated_code
    @asset(required_resource_keys={"fancy_db"})
    def existing_asset(context: AssetExecutionContext) -> None:
        # This code is now broken because the resource is no longer a FancyDbClient
        # but it is a FancyDbResource.
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_broken_unmigrated_code

    defs = Definitions(
        assets=[new_asset, existing_asset],
        jobs=[
            define_asset_job("new_asset_job", "new_asset"),
            define_asset_job("existing_asset_job", "existing_asset"),
        ],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )

    return defs


def new_third_party_resource_fixed() -> Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None:
            ...

    # begin_new_third_party_resource_with_interface
    from dagster import (
        AssetExecutionContext,
        ConfigurableResource,
        IAttachDifferentObjectToOpContext,
        asset,
    )

    class FancyDbResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
        conn_string: str

        def get_object_to_set_on_execution_context(self) -> FancyDbClient:
            return self.get_client()

        def get_client(self) -> FancyDbClient:
            return FancyDbClient(self.conn_string)

    @asset
    def new_asset(fancy_db: FancyDbResource) -> None:
        client = fancy_db.get_client()
        client.execute_query("SELECT * FROM foo")

    @asset(required_resource_keys={"fancy_db"})
    def existing_asset(context: AssetExecutionContext) -> None:
        # This code now works because context.resources.fancy_db is now a FancyDbClient
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_new_third_party_resource_with_interface

    defs = Definitions(
        assets=[new_asset, existing_asset],
        jobs=[
            define_asset_job("new_asset_job", "new_asset"),
            define_asset_job("existing_asset_job", "existing_asset"),
        ],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )

    return defs

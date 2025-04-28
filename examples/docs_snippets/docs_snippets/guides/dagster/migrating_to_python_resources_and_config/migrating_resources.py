from collections.abc import Iterator

import dagster as dg


def initial_code_base() -> dg.Definitions:
    # begin_initial_codebase
    import dagster as dg

    class FancyDbResource:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute(self, query: str) -> None: ...

    @dg.resource(config_schema={"conn_string": str})
    def fancy_db_resource(context: dg.InitResourceContext) -> FancyDbResource:
        return FancyDbResource(context.resource_config["conn_string"])

    @dg.asset(required_resource_keys={"fancy_db"})
    def asset_one(context: dg.AssetExecutionContext) -> None:
        assert context.resources.fancy_db

    @dg.asset(required_resource_keys={"fancy_db"})
    def asset_two(context: dg.AssetExecutionContext) -> None:
        assert context.resources.fancy_db

    defs = dg.Definitions(
        assets=[asset_one, asset_two],
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "some_value"})
        },
    )
    # end_initial_codebase
    return defs


def convert_resource() -> dg.Definitions:
    # begin_convert_resource
    import dagster as dg

    class FancyDbResource(dg.ConfigurableResource):
        conn_string: str

        def execute(self, query: str) -> None: ...

    # end_convert_resource

    # begin_resource_adapter
    import dagster as dg

    @dg.resource(config_schema=FancyDbResource.to_config_schema())
    def fancy_db_resource(context: dg.InitResourceContext) -> FancyDbResource:
        return FancyDbResource.from_resource_context(context)

    # old-style dg.resource API still works, but the Pythonic dg.resource is the source of truth
    # for schema information and implementation
    defs = dg.Definitions(
        # ...
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "some_value"})
        },
    )
    # end_resource_adapter

    return defs


def new_style_resource_on_context() -> dg.Definitions:
    # begin_new_style_resource_on_context
    import dagster as dg

    class FancyDbResource(dg.ConfigurableResource):
        conn_string: str

        def execute(self, query: str) -> None: ...

    @dg.asset(required_resource_keys={"fancy_db"})
    def asset_one(context: dg.AssetExecutionContext) -> None:
        # this still works because the dg.resource is still available on the context
        assert context.resources.fancy_db

    defs = dg.Definitions(
        assets=[asset_one],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )

    # end_new_style_resource_on_context

    return defs


def new_style_resource_on_param() -> dg.Definitions:
    import dagster as dg

    class FancyDbResource(dg.ConfigurableResource):
        conn_string: str

        def execute(self, query: str) -> None: ...

    # begin_new_style_resource_on_param
    import dagster as dg

    @dg.asset
    def asset_one(context: dg.AssetExecutionContext, fancy_db: FancyDbResource) -> None:
        assert fancy_db

    # end_new_style_resource_on_param

    return dg.Definitions(
        assets=[asset_one],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )


def old_third_party_resource() -> dg.Definitions:
    # begin_old_third_party_resource

    # Pre-existing code that you don't want to alter
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None: ...

    # Alternatively could have been imported from third-party library
    # from fancy_db import FancyDbClient
    import dagster as dg

    @dg.resource(config_schema={"conn_string": str})
    def fancy_db_resource(context: dg.InitResourceContext) -> FancyDbClient:
        return FancyDbClient(context.resource_config["conn_string"])

    @dg.asset(required_resource_keys={"fancy_db"})
    def existing_asset(context: dg.AssetExecutionContext) -> None:
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_old_third_party_resource

    defs = dg.Definitions(
        assets=[existing_asset],
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "something"})
        },
    )

    return defs


def some_expensive_setup() -> None: ...


def some_expensive_teardown() -> None: ...


def old_resource_code_contextmanager() -> dg.Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None: ...

    # begin_old_resource_code_contextmanager
    import dagster as dg

    @dg.resource(config_schema={"conn_string": str})
    def fancy_db_resource(context: dg.InitResourceContext) -> Iterator[FancyDbClient]:
        some_expensive_setup()
        try:
            # the client is yielded to the assets that require it
            yield FancyDbClient(context.resource_config["conn_string"])
        finally:
            # this is only called once the dg.asset has finished executing
            some_expensive_teardown()

    @dg.asset(required_resource_keys={"fancy_db"})
    def asset_one(context: dg.AssetExecutionContext) -> None:
        # some_expensive_setup() has been called, but some_expensive_teardown() has not
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_old_resource_code_contextmanager

    return dg.Definitions(
        assets=[asset_one],
        resources={
            "fancy_db": fancy_db_resource.configured({"conn_string": "something"})
        },
    )


def new_resource_code_contextmanager() -> dg.Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None: ...

    # begin_new_resource_code_contextmanager
    from contextlib import contextmanager

    import dagster as dg

    class FancyDbResource(dg.ConfigurableResource):
        conn_string: str

        @contextmanager
        def get_client(self) -> Iterator[FancyDbClient]:
            try:
                some_expensive_setup()
                yield FancyDbClient(self.conn_string)
            finally:
                some_expensive_teardown()

    @dg.asset
    def asset_one(fancy_db: FancyDbResource) -> None:
        with fancy_db.get_client() as client:
            client.execute_query("SELECT * FROM foo")

    # end_new_resource_code_contextmanager

    return dg.Definitions(
        assets=[asset_one],
        resources={"fancy_db": FancyDbResource(conn_string="something")},
    )


def new_third_party_resource_old_code_broken() -> dg.Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None: ...

    # begin_new_third_party_resource
    import dagster as dg

    class FancyDbResource(dg.ConfigurableResource):
        conn_string: str

        def get_client(self) -> FancyDbClient:
            return FancyDbClient(self.conn_string)

    @dg.asset
    def new_asset(fancy_db: FancyDbResource) -> None:
        client = fancy_db.get_client()
        client.execute_query("SELECT * FROM foo")

    # end_new_third_party_resource

    # begin_broken_unmigrated_code
    @dg.asset(required_resource_keys={"fancy_db"})
    def existing_asset(context: dg.AssetExecutionContext) -> None:
        # This code is now broken because the dg.resource is no longer a FancyDbClient
        # but it is a FancyDbResource.
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_broken_unmigrated_code

    defs = dg.Definitions(
        assets=[new_asset, existing_asset],
        jobs=[
            dg.define_asset_job("new_asset_job", "new_asset"),
            dg.define_asset_job("existing_asset_job", "existing_asset"),
        ],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )

    return defs


def new_third_party_resource_fixed() -> dg.Definitions:
    class FancyDbClient:
        def __init__(self, conn_string: str) -> None:
            self.conn_string = conn_string

        def execute_query(self, query: str) -> None: ...

    # begin_new_third_party_resource_with_interface
    import dagster as dg

    class FancyDbResource(
        dg.ConfigurableResource, dg.IAttachDifferentObjectToOpContext
    ):
        conn_string: str

        def get_object_to_set_on_execution_context(self) -> FancyDbClient:
            return self.get_client()

        def get_client(self) -> FancyDbClient:
            return FancyDbClient(self.conn_string)

    @dg.asset
    def new_asset(fancy_db: FancyDbResource) -> None:
        client = fancy_db.get_client()
        client.execute_query("SELECT * FROM foo")

    @dg.asset(required_resource_keys={"fancy_db"})
    def existing_asset(context: dg.AssetExecutionContext) -> None:
        # This code now works because context.resources.fancy_db is now a FancyDbClient
        context.resources.fancy_db.execute_query("SELECT * FROM foo")

    # end_new_third_party_resource_with_interface

    defs = dg.Definitions(
        assets=[new_asset, existing_asset],
        jobs=[
            dg.define_asset_job("new_asset_job", "new_asset"),
            dg.define_asset_job("existing_asset_job", "existing_asset"),
        ],
        resources={"fancy_db": FancyDbResource(conn_string="some_value")},
    )

    return defs

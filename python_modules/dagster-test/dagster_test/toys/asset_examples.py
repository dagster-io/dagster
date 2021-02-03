from contextlib import contextmanager
from typing import Callable, List, Optional

from dagster import (
    AssetKey,
    IOManager,
    IOManagerDefinition,
    InputDefinition,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    io_manager,
    pipeline,
    solid,
)
from pandas import DataFrame, read_csv


def io_manager_from_functions(
    handle_output_fn: Callable,
    load_input_fn: Callable,
    output_asset_keys_fn: Callable,
    input_asset_keys_fn: Optional[Callable] = None,
) -> IOManagerDefinition:
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            return handle_output_fn(context, obj)

        def load_input(self, context):
            return load_input_fn(context)

        def get_output_asset_keys(self, context):
            return output_asset_keys_fn(context)

        def get_input_asset_keys(self, context):
            if input_asset_keys_fn:
                return input_asset_keys_fn(context)
            else:
                return self.get_output_asset_keys(context)

    @io_manager
    def my_io_manager():
        return MyIOManager()

    return my_io_manager


def mode_defs_from_io_functions(
    handle_output_fn: Callable,
    load_input_fn: Callable,
    output_asset_keys_fn: Callable,
    input_asset_keys_fn: Optional[Callable] = None,
) -> List[ModeDefinition]:
    return [
        ModeDefinition(
            resource_defs={
                "io_manager": io_manager_from_functions(
                    handle_output_fn, load_input_fn, output_asset_keys_fn, input_asset_keys_fn
                )
            }
        )
    ]


def overwrite_partition(
    df: DataFrame, path: str, partition_name: str  # pylint: disable=unused-argument
) -> None:
    pass


def overwrite_partitions(
    df: DataFrame,  # pylint: disable=unused-argument
    path: str,  # pylint: disable=unused-argument
    partition_name: str,  # pylint: disable=unused-argument
    num_partitions: int,  # pylint: disable=unused-argument
) -> None:
    pass


def read_partition(path: str, partition_name: str) -> DataFrame:  # pylint: disable=unused-argument
    pass


def read_partitions(
    path: str, latest_partition_name: str, num_partitions: int  # pylint: disable=unused-argument
) -> DataFrame:
    pass


def earlier_partition(
    partition_name: str, num_earlier: int  # pylint: disable=unused-argument
) -> str:
    pass


@contextmanager
def db_connection():
    pass


def pure_drop_recreate():
    """
    "Pure" means that the solid bodies contain only business logic, and IO is delegated to an IO
    manager.

    Drop/recreate means that the steps overwrite entire tables, rather than single partitions.
    The solids also take entire tables as input.
    """

    def handle_output(context, obj):
        obj.to_csv(context.step_key)

    def load_input(context):
        return read_csv(context.upstream_output.step_key)

    def get_output_asset_keys(context):
        return [AssetKey([context.step_key])]

    @solid
    def solid1(_):
        return DataFrame()

    @solid
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(
        mode_defs=mode_defs_from_io_functions(handle_output, load_input, get_output_asset_keys)
    )
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def pure_single_partition():
    """
    "Pure" means that the solid bodies contain only business logic, and IO is delegated to an IO
    manager.

    Single partition means that the solid outputs replace single partitions of tables, rather than
    entire tables
    The solids also take single partitions of the upstream table as input.
    """

    def handle_output(context, obj):
        overwrite_partition(obj, context.step_key, context.config["partition"])

    def load_input(context):
        return read_partition(
            context.upstream_output.step_key, context.upstream_output.config["partition"]
        )

    def get_output_asset_keys(context):
        return [AssetKey([context.step_key], partition=context.config["partition"])]

    @solid
    def solid1(_):
        return DataFrame()

    @solid
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(
        mode_defs=mode_defs_from_io_functions(handle_output, load_input, get_output_asset_keys)
    )
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def pure_upstream_single_partition_downstream_drop_recreate():
    """
    "Pure" means that the solid bodies contain only business logic, and IO is delegated to an IO
    manager.

    The first step in this pipeline writes to a single partition of a table.  The second step
    reads that entire table (not just the partition written by the first step) and then overwrites
    an entire downstream table.
    """

    def handle_output(context, obj):
        overwrite_mode = context.metadata["overwrite_mode"]
        if overwrite_mode == "single_partition":
            overwrite_partition(obj, context.step_key, context.resource_config["partition"])
        elif overwrite_mode == "full_table":
            obj.to_csv(context.step_key)
        else:
            raise ValueError(f"invalid overwrite mode: {overwrite_mode}")

    def load_input(context):
        read_mode = context.metadata["read_mode"]
        if read_mode == "single_partition":
            return read_partition(
                context.upstream_output.step_key, context.resource_config["partition"]
            )
        elif read_mode == "full_table":
            return read_csv(context.step_key)
        else:
            raise ValueError(f"invalid read mode: {read_mode}")

    def get_output_asset_keys(context):
        overwrite_mode = context.metadata["overwrite_mode"]
        if overwrite_mode == "single_partition":
            return [AssetKey([context.step_key], partition=context.resource_config["partition"])]
        elif overwrite_mode == "full_table":
            return [AssetKey([context.step_key])]
        else:
            raise ValueError(f"invalid overwrite mode: {overwrite_mode}")

    def get_input_asset_keys(context):
        read_mode = context.metadata["read_mode"]
        if read_mode == "single_partition":
            return [AssetKey([context.step_key], partition=context.resource_config["partition"])]
        elif read_mode == "full_table":
            return [AssetKey([context.step_key])]
        else:
            raise ValueError(f"invalid read mode: {read_mode}")

    @solid(output_defs=[OutputDefinition(metadata={"overwrite_mode": "single_partition"})])
    def solid1(_):
        return DataFrame()

    @solid(
        input_defs=[InputDefinition("df", metadata={"read_mode": "full_table"})],
        output_defs=[OutputDefinition(metadata={"overwrite_mode": "full_table"})],
    )
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(
        mode_defs=mode_defs_from_io_functions(
            handle_output, load_input, get_output_asset_keys, get_input_asset_keys
        )
    )
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def pure_upstream_rolling_window_downstream_single_partition():
    """
    "Pure" means that the solid bodies contain only business logic, and IO is delegated to an IO
    manager.

    The first step in this pipeline overwrites a single partition of a table.

    The second step reads the last three partitions of that table and then overwrites a single
    partition of a downstream table.

    This might make sense if values in the second table depend on events that may have happened
    earlier in time.  E.g. the second table might have a column that indicates whether the user
    has logged in in the last three days.
    """

    def handle_output(context, obj):
        overwrite_partition(obj, context.step_key, context.resource_config["partition"])

    def load_input(context):
        return read_partitions(
            context.upstream_output.step_key,
            context.resource_config["partition"],
            context.metadata["num_partitions"],
        )

    def get_output_asset_keys(context):
        return [AssetKey([context.step_key], partition=context.resource_config["partition"])]

    def get_input_asset_keys(context):
        return [
            AssetKey(
                [context.upstream_output.step_key],
                partition=earlier_partition(context.resource_config["partition"], i),
            )
            for i in range(context.metadata["num_partitions"])
        ]

    @solid
    def solid1(_):
        return DataFrame()

    @solid(input_defs=[InputDefinition("df", metadata={"num_partitions": 3})])
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(
        mode_defs=mode_defs_from_io_functions(
            handle_output, load_input, get_output_asset_keys, get_input_asset_keys
        )
    )
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def pure_upstream_single_partition_downstream_rolling_window():
    """
    "Pure" means that the solid bodies contain only business logic, and IO is delegated to an IO
    manager.

    The first step in this pipeline overwrites a single partition of a table.

    The second step reads the last three partitions of that table and then overwrites the last three
    partitions of a downstream table.

    This might make sense if values in the second table depend on events that may have happened
    later in time.  E.g. the second table might have a column that indicates whether a credit card
    transaction was charged back.
    """

    def handle_output(context, obj):
        overwrite_partitions(
            obj,
            context.step_key,
            context.resource_config["partition"],
            context.metadata["num_partitions"],
        )

    def load_input(context):
        return read_partitions(
            context.upstream_output.step_key,
            context.resource_config["partition"],
            context.metadata["num_partitions"],
        )

    def get_output_asset_keys(context):
        return [
            AssetKey(
                [context.step_key],
                partition=earlier_partition(context.resource_config["partition"], i),
            )
            for i in range(context.metadata["num_partitions"])
        ]

    def get_input_asset_keys(context):
        return [
            AssetKey(
                [context.upstream_output.step_key],
                partition=earlier_partition(context.resource_config["partition"], i),
            )
            for i in range(context.metadata["num_partitions"])
        ]

    @solid(output_defs=[OutputDefinition(metadata={"num_partitions": 1})])
    def solid1(_):
        return DataFrame()

    @solid(
        input_defs=[InputDefinition("df", metadata={"num_partitions": 3})],
        output_defs=[OutputDefinition(metadata={"num_partitions": 3})],
    )
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(
        mode_defs=mode_defs_from_io_functions(
            handle_output, load_input, get_output_asset_keys, get_input_asset_keys
        )
    )
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def impure_drop_recreate():
    """
    "Impure" means that the solid body mixes business logic and IO.

    Drop/recreate means that the steps overwrite entire tables, rather than single partitions.
    The solids also take entire tables as input.
    """

    @solid(
        output_defs=OutputDefinition(
            dagster_type=Nothing, asset_key_fn=lambda _: [AssetKey(["solid1"])]
        )
    )
    def solid1(_):
        with db_connection() as con:
            con.execute(
                """
                create table solid1 as
                select * from source_table
                """
            )

    @solid(
        input_defs=[InputDefinition("solid1", dagster_type=Nothing)],
        output_defs=OutputDefinition(
            dagster_type=Nothing, asset_key_fn=lambda _: [AssetKey(["solid2"])]
        ),
    )
    def solid2(_):
        with db_connection() as con:
            con.execute(
                """
                create table solid2 as
                select * from solid1
                where some_condition
                """
            )

    @pipeline
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def impure_single_partition():
    """
    "Impure" means that the solid body mixes business logic and IO.

    Single partition means that the solid outputs replace single partitions of tables, rather than
    entire tables
    The solids also take single partitions of the upstream table as input.
    """

    def get_asset_keys(context):
        return [AssetKey([context.step_key], partition=context.solid_config["partition"])]

    @solid(
        config_schema={"partition": str},
        output_defs=OutputDefinition(dagster_type=Nothing, asset_key_fn=get_asset_keys),
    )
    def solid1(context) -> Nothing:
        with db_connection() as con:
            con.execute(
                f"""
                delete from table solid1
                where partition = {context.solid_config["partition"]}
                """
            )
            con.execute(
                f"""
                insert into solid1 as
                select * from source_table
                where partition = {context.solid_config["partition"]}
                """
            )

    @solid(
        config_schema={"partition": str},
        input_defs=[InputDefinition("solid1", dagster_type=Nothing)],
        output_defs=OutputDefinition(dagster_type=Nothing, asset_key_fn=get_asset_keys),
    )
    def solid2(context):
        with db_connection() as con:
            con.execute(
                f"""
                delete from table solid2
                where partition = {context.solid_config["partition"]}
                """
            )
            con.execute(
                f"""
                insert into solid2
                select * from solid1
                where partition = {context.solid_config["partition"]}
                    and some_condition
                """
            )

    @pipeline
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def impure_upstream_single_partition_downstream_drop_recreate():
    """
    "Impure" means that the solid body mixes business logic and IO.

    The first step in this pipeline writes to a single partition of a table.  The second step
    reads that entire table (not just the partition written by the first step) and then overwrites
    an entire downstream table.
    """

    @solid(
        config_schema={"partition": str},
        output_defs=[
            OutputDefinition(
                dagster_type=Nothing,
                asset_key_fn=lambda context: [
                    AssetKey(["solid1"], partition=context.solid_config["partition"])
                ],
            )
        ],
    )
    def solid1(context):
        with db_connection() as con:
            con.execute(
                f"""
                delete from table solid1
                where partition = {context.solid_config["partition"]}
                """
            )
            con.execute(
                f"""
                insert into solid1
                select * from source_table
                where partition = {context.solid_config["partition"]}
                """
            )

    @solid(
        output_defs=[
            OutputDefinition(dagster_type=Nothing, asset_key_fn=lambda _: [AssetKey(["solid2"])],)
        ],
        input_defs=[
            InputDefinition(
                "solid1", dagster_type=Nothing, asset_key_fn=lambda _: [AssetKey(["solid1"])]
            )
        ],
    )
    def solid2(_):
        with db_connection() as con:
            con.execute(
                """
                create table solid2 as
                select * from solid1
                where some_condition
                """
            )

    @pipeline
    def my_pipeline():
        solid2(solid1())

    return my_pipeline

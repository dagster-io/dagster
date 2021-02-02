from contextlib import contextmanager
from typing import Callable, List

from dagster import (
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
    handle_output_fn: Callable, load_input_fn: Callable
) -> IOManagerDefinition:
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            return handle_output_fn(context, obj)

        def load_input(self, context):
            return load_input_fn(context)

    @io_manager
    def my_io_manager():
        return MyIOManager()

    return my_io_manager


def mode_defs_from_io_functions(
    handle_output_fn: Callable, load_input_fn: Callable
) -> List[ModeDefinition]:
    return [
        ModeDefinition(
            resource_defs={"io_manager": io_manager_from_functions(handle_output_fn, load_input_fn)}
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

    @solid
    def solid1(_):
        return DataFrame()

    @solid
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(mode_defs=mode_defs_from_io_functions(handle_output, load_input))
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

    @solid
    def solid1(_):
        return DataFrame()

    @solid
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(mode_defs=mode_defs_from_io_functions(handle_output, load_input))
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

    @solid(output_defs=[OutputDefinition(metadata={"overwrite_mode": "single_partition"})])
    def solid1(_):
        return DataFrame()

    @solid(
        input_defs=[InputDefinition("df", metadata={"read_mode": "full_table"})],
        output_defs=[OutputDefinition(metadata={"overwrite_mode": "full_table"})],
    )
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(mode_defs=mode_defs_from_io_functions(handle_output, load_input))
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

    @solid
    def solid1(_):
        return DataFrame()

    @solid(input_defs=[InputDefinition("df", metadata={"num_partitions": 3})])
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(mode_defs=mode_defs_from_io_functions(handle_output, load_input))
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

    @solid(output_defs=[OutputDefinition(metadata={"num_partitions": 1})])
    def solid1(_):
        return DataFrame()

    @solid(
        input_defs=[InputDefinition("df", metadata={"num_partitions": 3})],
        output_defs=[OutputDefinition(metadata={"num_partitions": 3})],
    )
    def solid2(_, df):
        return df[df["some_condition"]]

    @pipeline(mode_defs=mode_defs_from_io_functions(handle_output, load_input))
    def my_pipeline():
        solid2(solid1())

    return my_pipeline


def impure_drop_recreate():
    """
    "Impure" means that the solid body mixes business logic and IO.

    Drop/recreate means that the steps overwrite entire tables, rather than single partitions.
    The solids also take entire tables as input.
    """

    @solid
    def solid1(_) -> Nothing:
        with db_connection() as con:
            con.execute(
                """
                create table solid1 as
                select * from source_table
                """
            )

    @solid(input_defs=[InputDefinition("solid1", dagster_type=Nothing)])
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

    @solid(config_schema={"partition": str})
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
        input_defs=[InputDefinition("solid1", dagster_type=Nothing)],
        config_schema={"partition": str},
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

    @solid(config_schema={"partition": str})
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
                insert into solid1
                select * from source_table
                where partition = {context.solid_config["partition"]}
                """
            )

    @solid(input_defs=[InputDefinition("solid1", dagster_type=Nothing)])
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

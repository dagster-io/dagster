from dagster import Array, Bool, Field, In, Nothing, Out, Output, op

from .types import DbtOutput
from .utils import generate_events, generate_materializations

_DEFAULT_OP_PROPS = dict(
    required_resource_keys={"dbt"},
    ins={"start_after": In(Nothing)},
    out=Out(DbtOutput, description="Parsed output from running the dbt command."),
    tags={"kind": "dbt"},
)


def _get_doc(op_name: str, dbt_command: str) -> str:
    return f"""
This op executes a ``dbt {dbt_command}`` command. It requires the use of a dbt resource, which can be
set to execute this command through the CLI (using the :py:class:`~dagster_dbt.dbt_cli_resource`) or
over RPC (using the :py:class:`~dbt_rpc_sync_resource`).

Examples:

.. code-block:: python

    from dagster import job
    from dagster_dbt import {op_name}, dbt_cli_resource, dbt_rpc_sync_resource

    @job(resource_defs={{"dbt":dbt_cli_resource}})
    def my_dbt_cli_job():
        {op_name}()

    @job(resource_defs={{"dbt":dbt_rpc_sync_resource}})
    def my_dbt_rpc_job():
        {op_name}()
    """


# NOTE: mypy fails to properly track the type of `_DEFAULT_OP_PROPS` items when they are
# double-splatted, so we type-ignore the below op declarations.


@op(  # type: ignore
    **_DEFAULT_OP_PROPS,
    config_schema={
        "yield_asset_events": Field(
            config=Bool,
            default_value=True,
            description=(
                "If True, materializations and asset observations corresponding to the results of "
                "the dbt operation will be yielded when the op executes. Default: True"
            ),
        ),
        "asset_key_prefix": Field(
            config=Array(str),
            default_value=["dbt"],
            description=(
                "If provided and yield_materializations is True, these components will be used to "
                "prefix the generated asset keys."
            ),
        ),
    },
)
def dbt_build_op(context):
    dbt_output = context.resources.dbt.build()
    if context.op_config["yield_asset_events"] and "results" in dbt_output.result:
        yield from generate_events(
            dbt_output,
            node_info_to_asset_key=lambda info: context.op_config["asset_key_prefix"]
            + info["unique_id"].split("."),
            manifest_json=context.resources.dbt.get_manifest_json(),
        )
    yield Output(dbt_output)


@op(  # type: ignore
    **_DEFAULT_OP_PROPS,
    config_schema={
        "yield_materializations": Field(
            config=Bool,
            default_value=True,
            description=(
                "If True, materializations corresponding to the results of the dbt operation will "
                "be yielded when the op executes. Default: True"
            ),
        ),
        "asset_key_prefix": Field(
            config=Array(str),
            default_value=["dbt"],
            description=(
                "If provided and yield_materializations is True, these components will be used to "
                "prefix the generated asset keys."
            ),
        ),
    },
)
def dbt_run_op(context):
    dbt_output = context.resources.dbt.run()
    if context.op_config["yield_materializations"] and "results" in dbt_output.result:
        yield from generate_materializations(
            dbt_output, asset_key_prefix=context.op_config["asset_key_prefix"]
        )
    yield Output(dbt_output)


@op(**_DEFAULT_OP_PROPS)  # type: ignore
def dbt_compile_op(context):
    return context.resources.dbt.compile()


@op(**_DEFAULT_OP_PROPS)  # type: ignore
def dbt_ls_op(context):
    return context.resources.dbt.ls()


@op(**_DEFAULT_OP_PROPS)  # type: ignore
def dbt_test_op(context):
    return context.resources.dbt.test()


@op(**_DEFAULT_OP_PROPS)  # type: ignore
def dbt_snapshot_op(context):
    return context.resources.dbt.snapshot()


@op(**_DEFAULT_OP_PROPS)  # type: ignore
def dbt_seed_op(context):
    return context.resources.dbt.seed()


@op(**_DEFAULT_OP_PROPS)  # type: ignore
def dbt_docs_generate_op(context):
    return context.resources.dbt.generate_docs()


for dbt_op, cmd in [
    (dbt_build_op, "build"),
    (dbt_run_op, "run"),
    (dbt_compile_op, "compile"),
    (dbt_ls_op, "ls"),
    (dbt_test_op, "test"),
    (dbt_snapshot_op, "snapshot"),
    (dbt_seed_op, "seed"),
    (dbt_docs_generate_op, "docs generate"),
]:
    dbt_op.__doc__ = _get_doc(dbt_op.name, cmd)

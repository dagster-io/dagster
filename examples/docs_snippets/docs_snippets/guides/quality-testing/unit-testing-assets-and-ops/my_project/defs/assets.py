# start_combo
import dagster as dg


class SeparatorConfig(dg.Config):
    separator: str


@dg.asset
def processed_file(
    primary_file: str, secondary_file: str, config: SeparatorConfig
) -> str:
    return f"{primary_file}{config.separator}{secondary_file}"


# end_combo


# start_config
import dagster as dg


class FilepathConfig(dg.Config):
    path: str


@dg.asset
def loaded_file(config: FilepathConfig) -> str:
    with open(config.path) as file:
        return file.read()


# end_config


# start_context
import dagster as dg


@dg.asset
def loaded_file(context: dg.AssetExecutionContext) -> str:
    return context.partition_key


# end_context


# start_dependency
import dagster as dg


@dg.asset
def loaded_file() -> str:
    with open("path.txt") as file:
        return file.read()


@dg.asset
def processed_file(loaded_file: str) -> str:
    return loaded_file.strip()


# end_dependency


# start_no_argument
import dagster as dg


@dg.asset
def loaded_file() -> str:
    with open("path.txt") as file:
        return file.read()


# end_no_argument


# start_resource
from dagster_aws.s3 import S3FileHandle, S3FileManager

import dagster as dg


@dg.asset
def loaded_file(file_manager: S3FileManager) -> str:
    return file_manager.read_data(S3FileHandle("bucket", "path.txt"))


# end_resource


# start_op
import dagster as dg


class SeparatorConfig(dg.Config):
    separator: str


@dg.op
def process_file(
    primary_file: str, secondary_file: str, config: SeparatorConfig
) -> str:
    return f"{primary_file}{config.separator}{secondary_file}"


# end_op


# start_op_config
import dagster as dg


class FilepathConfig(dg.Config):
    path: str


@dg.op
def load_file(config: FilepathConfig) -> str:
    with open(config.path) as file:
        return file.read()


# end_op_config


# start_op_context
import dagster as dg


@dg.op
def load_file(context: dg.OpExecutionContext) -> str:
    with open(f"path_{context.partition_key}.txt") as file:
        return file.read()


# end_op_context


# start_op_dependency
import dagster as dg


@dg.op
def process_file(loaded_file: str) -> str:
    return loaded_file.strip()


# highlight-start
def test_process_file() -> None:
    assert process_file(" contents  ") == "contents"
    # highlight-end


# end_op_dependency


# start_op_no_argument
import dagster as dg


@dg.op
def load_file() -> str:
    with open("path.txt") as file:
        return file.read()


# end_op_no_argument


# start_op_resource
from dagster_aws.s3 import S3FileHandle, S3FileManager

import dagster as dg


@dg.op
def load_file(file_manager: S3FileManager) -> str:
    return file_manager.read_data(S3FileHandle("bucket", "path.txt"))


# end_op_resource

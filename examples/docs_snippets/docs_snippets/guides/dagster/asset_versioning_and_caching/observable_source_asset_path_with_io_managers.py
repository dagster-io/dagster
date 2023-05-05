import os
from hashlib import sha256
from typing import Any

from dagster import (
    DataVersion,
    Definitions,
    InputContext,
    IOManager,
    OutputContext,
    asset,
    file_relative_path,
    observable_source_asset,
)
from dagster._seven.temp_dir import get_system_temp_directory
from dagster._utils import mkdir_p


# This simulates the I/O manager for our internal data lake
class NumberTextFileIOManager(IOManager):
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    @staticmethod
    def with_directory(root_dir: str):
        mkdir_p(root_dir)
        return NumberTextFileIOManager(root_dir=root_dir)

    def load_input(self, context: "InputContext") -> int:
        asset_key_str = context.asset_key.to_user_string()

        full_path = os.path.join(self.root_dir, f"{asset_key_str}.txt")
        with open(full_path) as ff:
            return int(ff.read())

    def handle_output(self, context: "OutputContext", obj: int) -> None:
        # without writing a custom input manager and setting the key on if from the asset in
        # this function gets called by the observable source asset
        # dagster._core.errors.DagsterInvariantViolationError:
        # Attempting to access asset_key, but it was not provided when constructing the OutputContext
        # Even when you override the io_manager_key on the source asset, this is still called

        # The other option is to use the default i/o manager for the source asset
        # to that it writes pickled None somewhere and then use a custom i/o
        # manager key for all the other assets. Both are pretty bad.
        if context.op_def.name == "input_number":
            return

        asset_key_str = context.asset_key.to_user_string()

        full_path = os.path.join(self.root_dir, f"{asset_key_str}.txt")
        with open(full_path, "w") as ff:
            ff.write(str(obj))


def sha256_digest_from_str(string: str) -> str:
    hash_sig = sha256()
    hash_sig.update(bytearray(string, "utf8"))
    return hash_sig.hexdigest()


FILE_PATH = file_relative_path(__file__, "input_number.txt")


# knows how to load file that is dropped somewhere by an external process
class ExternalFileInputManager(IOManager):
    def load_input(self, context: "InputContext") -> object:
        with open(FILE_PATH) as ff:
            return int(ff.read())

    def handle_output(self, context: "OutputContext", obj: Any) -> None:
        raise Exception("This should never be called")


# in order to get the right input loading behavior for the downstream assets
# we need to use the external file input manager key here. pretty confusing when
# coming at this fresh
@observable_source_asset(io_manager_key="external_file_input_manager")
def input_number():
    with open(FILE_PATH) as ff:
        return DataVersion(sha256_digest_from_str(ff.read()))


@asset(code_version="v3")
def versioned_number(input_number):
    return input_number


@asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2


defs = Definitions(
    assets=[input_number, versioned_number, multiplied_number],
    resources={
        "io_manager": NumberTextFileIOManager.with_directory(
            os.path.join(get_system_temp_directory(), "versioning_example")
        ),
        "external_file_input_manager": ExternalFileInputManager(),
    },
)

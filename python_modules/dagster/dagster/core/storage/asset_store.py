import os
import pickle
from abc import ABCMeta, abstractmethod
from collections import namedtuple

import six
from dagster import check
from dagster.config import Field
from dagster.config.source import StringSource
from dagster.core.definitions.resource import resource
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.serdes import whitelist_for_serdes
from dagster.utils import PICKLE_PROTOCOL, mkdir_p


@whitelist_for_serdes
class AssetStoreHandle(namedtuple("_AssetStoreHandle", "asset_store_key asset_metadata")):
    def __new__(cls, asset_store_key, asset_metadata=None):
        return super(AssetStoreHandle, cls).__new__(
            cls,
            asset_store_key=check.str_param(asset_store_key, "asset_store_key"),
            asset_metadata=asset_metadata,
        )


class AssetStore(six.with_metaclass(ABCMeta)):
    """
    Base class for user-provided asset store.

    Extend this class to handle asset operations. Users should implement ``set_asset`` to write a
    data object that can be tracked by the Dagster machinery and ``get_asset`` to read an existing
    data object.
    """

    @abstractmethod
    def set_asset(self, context, step_output_handle, obj, asset_metadata):
        """The user-definied write method that stores a data object.

        Args:
            context (SystemStepExecutionContext): The context that the corresponding step is in.
            step_output_handle (StepOutputHandle): the handle of the step output which generates
                the asset.
            obj (Any): The data object to be stored.
            asset_metadata (Optional[Any]): The serializable metadata defined on the step that
                produced the given data object. For example, users can provide a file path if the
                data object will be stored in a filesystem, or provide information of a database
                table when it is going to load the data into the table.
        """

    @abstractmethod
    def get_asset(self, context, step_output_handle, asset_metadata):
        """The user-defined read method that loads data given its metadata.

        Args:
            context (SystemStepExecutionContext): The context that the corresponding step is in.
            step_output_handle (StepOutputHandle): the handle of the step output which generates
                the asset.
            asset_metadata (Optional[Any]): The metadata defined on the step that produced the
                data object to get.

        Returns:
            Any: The data object.
        """


class InMemoryAssetStore(AssetStore):
    def __init__(self):
        self.values = {}

    def set_asset(self, _context, step_output_handle, obj, _asset_metadata):
        self.values[step_output_handle] = obj

    def get_asset(self, _context, step_output_handle, _asset_metadata):
        return self.values[step_output_handle]


@resource
def mem_asset_store(_):
    return InMemoryAssetStore()


class PickledObjectFilesystemAssetStore(AssetStore):
    def __init__(self, base_dir=None):
        self.base_dir = check.opt_str_param(base_dir, "base_dir")
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, context, step_output_handle):
        # automatically construct filepath
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)

        return os.path.join(
            self.base_dir,
            context.run_id,
            step_output_handle.step_key,
            step_output_handle.output_name,
        )

    def set_asset(self, context, step_output_handle, obj, _asset_metadata):
        """Pickle the data and store the object to a file."""
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)

        filepath = self._get_path(context, step_output_handle)

        # Ensure path exists
        mkdir_p(os.path.dirname(filepath))

        with open(filepath, self.write_mode) as write_obj:
            pickle.dump(obj, write_obj, PICKLE_PROTOCOL)

    def get_asset(self, context, step_output_handle, _asset_metadata):
        """Unpickle the file and Load it to a data object."""
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)

        filepath = self._get_path(context, step_output_handle)

        with open(filepath, self.read_mode) as read_obj:
            return pickle.load(read_obj)


@resource(config_schema={"base_dir": Field(StringSource, default_value=".", is_required=False)})
def default_filesystem_asset_store(init_context):
    """Default asset store.

    It allows users to specify a base directory where all the step output will be stored in. It
    serializes and deserializes output values (assets) using pickling and automatically constructs
    the filepaths for the assets.
    """
    return PickledObjectFilesystemAssetStore(init_context.resource_config["base_dir"])


class CustomPathPickledObjectFilesystemAssetStore(AssetStore):
    def __init__(self, base_dir=None):
        self.base_dir = check.opt_str_param(base_dir, "base_dir")
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, path):
        return os.path.join(self.base_dir, path)

    def set_asset(self, _context, step_output_handle, obj, asset_metadata):
        """Pickle the data and store the object to a custom file path."""
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        path = check.str_param(asset_metadata.get("path"), "asset_metadata.path")

        filepath = self._get_path(path)

        # Ensure path exists
        mkdir_p(os.path.dirname(filepath))

        with open(filepath, self.write_mode) as write_obj:
            pickle.dump(obj, write_obj, PICKLE_PROTOCOL)

    def get_asset(self, _context, step_output_handle, asset_metadata):
        """Unpickle the file from a given file path and Load it to a data object."""
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        path = check.str_param(asset_metadata.get("path"), "asset_metadata.path")
        filepath = self._get_path(path)

        with open(filepath, self.read_mode) as read_obj:
            return pickle.load(read_obj)


@resource(config_schema={"base_dir": Field(StringSource, default_value=".", is_required=False)})
def custom_path_filesystem_asset_store(init_context):
    """Built-in asset store that allows users to custom output file path per output definition.

    It also allows users to specify a base directory where all the step output will be stored in. It
    serializes and deserializes output values (assets) using pickling and stores the pickled object
    in the user-provided file paths.
    """
    return CustomPathPickledObjectFilesystemAssetStore(init_context.resource_config["base_dir"])

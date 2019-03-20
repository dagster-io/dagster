import os
import pickle

from dagster import check, seven
from dagster.utils import mkdir_p

from .execution_context import SystemPipelineExecutionContext
from .types.runtime import RuntimeType


class ObjectStore:
    pass


class FileSystemObjectStore(ObjectStore):
    def __init__(self, run_id):
        check.str_param(run_id, 'run_id')
        self.root = os.path.join(
            seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
        )

    def set_object(self, obj, context, runtime_type, paths):  # pylint: disable=unused-argument
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        if len(paths) > 1:
            target_dir = os.path.join(self.root, *paths[:-1])
            mkdir_p(target_dir)
            target_path = os.path.join(target_dir, paths[-1])
        else:
            check.invariant(len(paths) == 1)
            target_dir = self.root
            mkdir_p(target_dir)
            target_path = os.path.join(target_dir, paths[0])

        check.invariant(not os.path.exists(target_path))
        with open(target_path, 'wb') as ff:
            # Hardcode pickle for now
            pickle.dump(obj, ff)

    def get_object(self, context, runtime_type, paths):  # pylint: disable=unused-argument
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        target_path = os.path.join(self.root, *paths)
        with open(target_path, 'rb') as ff:
            return pickle.load(ff)

    def has_object(self, _cxt, paths):
        target_path = os.path.join(self.root, *paths)
        return os.path.exists(target_path)

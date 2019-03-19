from abc import ABCMeta, abstractmethod
from collections import namedtuple
from contextlib import contextmanager
import pickle
import os

import six

from dagster import check
from dagster import seven
from dagster.utils import mkdir_p


class StepOutputHandle(namedtuple('_StepOutputHandle', 'step_key output_name')):
    @staticmethod
    def from_step(step, output_name):
        from .objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)

        return StepOutputHandle(step.key, output_name)

    def __new__(cls, step_key, output_name):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step_key=check.str_param(step_key, 'step_key'),
            output_name=check.str_param(output_name, 'output_name'),
        )


def read_pickle_file(path):
    check.str_param(path, 'path')
    with open(path, 'rb') as ff:
        return pickle.load(ff)


def write_pickle_file(path, value):
    check.str_param(path, 'path')
    with open(path, 'wb') as ff:
        return pickle.dump(value, ff)


class IntermediatesManager(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def get_intermediate(self, step_output_handle):
        pass

    @abstractmethod
    def set_intermediate(self, step_output_handle, value):
        pass

    @abstractmethod
    def has_value(self, step_output_handle):
        pass

    def all_inputs_covered(self, step):
        from .objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)
        for step_input in step.step_inputs:
            if not self.has_value(step_input.prev_output_handle):
                return False
        return True


class InMemoryIntermediatesManager(IntermediatesManager):
    def __init__(self):
        self.values = {}

    def get_intermediate(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return self.values[step_output_handle]

    def set_intermediate(self, step_output_handle, value):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        self.values[step_output_handle] = value

    def has_value(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return step_output_handle in self.values


class FileStoreIntermediatesManager(IntermediatesManager):
    def __init__(self, run_id):
        self._object_store = NewTempObjectStore(run_id)
        # self._files = LocalTempFileStore(run_id)

    def _get_path_comps(self, step_output_handle):
        return ['intermediates', step_output_handle.step_key, step_output_handle.output_name]

    def get_intermediate(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(self.has_value(step_output_handle))

        return self._object_store.get_object(
            _cxt=None, _runtime_type=None, paths=self._get_path_comps(step_output_handle)
        )

    def set_intermediate(self, step_output_handle, value):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(not self.has_value(step_output_handle))

        return self._object_store.set_object(
            obj=value, _cxt=None, _runtime_type=None, paths=self._get_path_comps(step_output_handle)
        )

    def has_value(self, step_output_handle):
        return self._object_store.has_object(
            _cxt=None, paths=self._get_path_comps(step_output_handle)
        )


class NewTempObjectStore:
    def __init__(self, run_id):
        check.str_param(run_id, 'run_id')
        self.root = os.path.join(
            seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
        )

    def set_object(self, obj, _cxt, _runtime_type, paths):
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        if len(paths) > 1:
            target_dir = os.path.join(self.root, *paths[:-1])
            mkdir_p(target_dir)
            target_path = os.path.join(target_dir, paths[-1])
        else:
            check.invariant(len(paths) == 1)
            target_path = os.path.join(target_dir, paths[0])

        check.invariant(not os.path.exists(target_path))
        with open(target_path, 'wb') as ff:
            # Hardcode pickle for now
            pickle.dump(obj, ff)

    def get_object(self, _cxt, _runtime_type, paths):
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        target_path = os.path.join(self.root, *paths)
        with open(target_path, 'rb') as ff:
            return pickle.load(ff)

    def has_object(self, _cxt, paths):
        target_path = os.path.join(self.root, *paths)
        return os.path.exists(target_path)


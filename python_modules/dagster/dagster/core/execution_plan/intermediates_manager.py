from abc import ABCMeta, abstractmethod
from collections import namedtuple
from contextlib import contextmanager
import pickle
import os

import six

from dagster import check
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
    def get_value(self, step_output_handle):
        pass

    @abstractmethod
    def set_value(self, step_output_handle, value):
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

    def get_value(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return self.values[step_output_handle]

    def set_value(self, step_output_handle, value):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        self.values[step_output_handle] = value

    def has_value(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return step_output_handle in self.values


# TODO: This should go through persistence and serialization infrastructure
# Fixing this requires getting the type information (serialization_strategy is
# a property of runtime type) of the step output you are dealing with. As things
# are structured now we construct the inputs before execution. The fix to this
# will likely be to inject a different type of execution step that threads
# the manager
class FileSystemIntermediateManager(IntermediatesManager):
    def __init__(self, run_id):
        self._files = LocalTempFileStore(run_id)

    def _get_path_comps(self, step_output_handle):
        return ['intermediates', step_output_handle.step_key, step_output_handle.output_name]

    def get_value(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(self.has_value(step_output_handle))

        with self._files.readable_binary_stream(*self._get_path_comps(step_output_handle)) as ff:
            return pickle.load(ff)

    def set_value(self, step_output_handle, value):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(not self.has_value(step_output_handle))

        with self._files.writeable_binary_stream(*self._get_path_comps(step_output_handle)) as ff:
            pickle.dump(value, ff)

    def has_value(self, step_output_handle):
        return self._files.has_file(*self._get_path_comps(step_output_handle))


def check_path_comps(path_comps):
    path_list = check.list_param(list(path_comps), 'path_comps', of_type=str)
    check.param_invariant(path_list, 'path_list', 'Must have at least one comp')
    return path_list


class LocalTempFileStore:
    def __init__(self, run_id):
        check.str_param(run_id, 'run_id')
        self.root = os.path.join('/tmp', 'dagster', 'runs', run_id, 'files')
        self._created = False

    def ensure_root_exists(self):
        if not self._created:
            mkdir_p(self.root)

        self._created = True

    @contextmanager
    def writeable_binary_stream(self, *path_comps):
        self.ensure_root_exists()

        path_list = check_path_comps(path_comps)

        target_dir = os.path.join(self.root, *path_list[:-1])
        mkdir_p(target_dir)

        target_path = os.path.join(target_dir, path_list[-1])
        check.invariant(not os.path.exists(target_path))
        with open(target_path, 'wb') as ff:
            yield ff

    @contextmanager
    def readable_binary_stream(self, *path_comps):
        self.ensure_root_exists()

        path_list = check_path_comps(path_comps)

        target_path = os.path.join(self.root, *path_list)
        with open(target_path, 'rb') as ff:
            yield ff

    def has_file(self, *path_comps):
        self.ensure_root_exists()

        path_list = check_path_comps(path_comps)

        target_path = os.path.join(self.root, *path_list)

        if os.path.exists(target_path):
            check.invariant(os.path.isfile(target_path))
            return True
        else:
            return False

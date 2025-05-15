import itertools
import os
import shutil
import tempfile
from contextlib import contextmanager

from dagster_shared.utils.temp_files import get_temp_file_name, unlink_swallow_errors

import dagster._check as check
from dagster._core.storage.file_manager import LocalFileHandle


@contextmanager
def get_temp_file_handle_with_data(data):
    with get_temp_file_name_with_data(data) as temp_file:
        yield LocalFileHandle(temp_file)


@contextmanager
def get_temp_file_name_with_data(data):
    with get_temp_file_name() as temp_file:
        with open(temp_file, "wb") as ff:
            ff.write(data)

        yield temp_file


@contextmanager
def get_temp_file_handle():
    with get_temp_file_name() as temp_file:
        yield LocalFileHandle(temp_file)


@contextmanager
def get_temp_file_names(number):
    check.int_param(number, "number")

    temp_file_names = list()
    for _ in itertools.repeat(None, number):
        handle, temp_file_name = tempfile.mkstemp()
        os.close(handle)  # # just need the name - avoid leaking the file descriptor
        temp_file_names.append(temp_file_name)

    try:
        yield tuple(temp_file_names)
    finally:
        for temp_file_name in temp_file_names:
            unlink_swallow_errors(temp_file_name)


@contextmanager
def get_temp_dir(in_directory=None):
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(dir=in_directory)
        yield temp_dir
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)

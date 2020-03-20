import contextlib
import datetime
import errno
import inspect
import multiprocessing
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
from collections import namedtuple
from enum import Enum
from warnings import warn

import yaml
from six.moves import configparser

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.seven import IS_WINDOWS, thread
from dagster.seven.abc import Mapping

from .yaml_utils import load_yaml_from_glob_list, load_yaml_from_globs, load_yaml_from_path

if sys.version_info > (3,):
    from pathlib import Path  # pylint: disable=import-error
else:
    from pathlib2 import Path  # pylint: disable=import-error

EPOCH = datetime.datetime.utcfromtimestamp(0)

PICKLE_PROTOCOL = 2


DEFAULT_REPOSITORY_YAML_FILENAME = 'repository.yaml'


def file_relative_path(dunderfile, relative_path):
    '''
    This function is useful when one needs to load a file that is
    relative to the position of the current file. (Such as when
    you encode a configuration file path in source file and want
    in runnable in any current working directory)

    It is meant to be used like the following:

    file_relative_path(__file__, 'path/relative/to/file')

    '''

    check.str_param(dunderfile, 'dunderfile')
    check.str_param(relative_path, 'relative_path')

    return os.path.join(os.path.dirname(dunderfile), relative_path)


def script_relative_path(file_path):
    '''
    Useful for testing with local files. Use a path relative to where the
    test resides and this function will return the absolute path
    of that file. Otherwise it will be relative to script that
    ran the test

    Note: this is function is very, very expensive (on the order of 1
    millisecond per invocation) so this should only be used in performance
    insensitive contexts. Prefer file_relative_path for anything with
    performance constraints.

    '''
    # from http://bit.ly/2snyC6s

    check.str_param(file_path, 'file_path')
    scriptdir = inspect.stack()[1][1]
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(scriptdir)), file_path))


# Adapted from https://github.com/okunishinishi/python-stringcase/blob/master/stringcase.py
def camelcase(string):
    check.str_param(string, 'string')

    string = re.sub(r'^[\-_\.]', '', str(string))
    if not string:
        return string
    return str(string[0]).upper() + re.sub(
        r'[\-_\.\s]([a-z])', lambda matched: str(matched.group(1)).upper(), string[1:]
    )


def ensure_single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict', 'Expected dict with single item')
    return list(ddict.items())[0]


@contextlib.contextmanager
def pushd(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(old_cwd)


def safe_isfile(path):
    '''"Backport of Python 3.8 os.path.isfile behavior.

    This is intended to backport https://docs.python.org/dev/whatsnew/3.8.html#os-path. I'm not
    sure that there are other ways to provoke this behavior on Unix other than the null byte,
    but there are certainly other ways to do it on Windows. Afaict, we won't mask other
    ValueErrors, and the behavior in the status quo ante is rough because we risk throwing an
    unexpected, uncaught ValueError from very deep in our logic.
    '''
    try:
        return os.path.isfile(path)
    except ValueError:
        return False


def mkdir_p(path):
    try:
        os.makedirs(path)
        return path
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def merge_dicts(left, right):
    check.dict_param(left, 'left')
    check.dict_param(right, 'right')

    result = left.copy()
    result.update(right)
    return result


class frozendict(dict):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("Cannot modify ReadOnlyDict")

    # https://docs.python.org/3/library/pickle.html#object.__reduce__
    #
    # For a dict, the default behavior for pickle is to iteratively call __setitem__ (see 5th item
    #  in __reduce__ tuple). Since we want to disable __setitem__ and still inherit dict, we
    # override this behavior by defining __reduce__. We return the 3rd item in the tuple, which is
    # passed to __setstate__, allowing us to restore the frozendict.

    def __reduce__(self):
        return (frozendict, (), dict(self))

    def __setstate__(self, state):
        self.__init__(state)

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    del __readonly__


class frozenlist(list):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("Cannot modify ReadOnlyList")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    append = __readonly__
    clear = __readonly__
    extend = __readonly__
    insert = __readonly__
    pop = __readonly__
    remove = __readonly__
    reverse = __readonly__
    sort = __readonly__


def make_readonly_value(value):
    if isinstance(value, list):
        return frozenlist(list(map(make_readonly_value, value)))
    elif isinstance(value, dict):
        return frozendict({key: make_readonly_value(value) for key, value in value.items()})
    else:
        return value


def get_prop_or_key(elem, key):
    if isinstance(elem, Mapping):
        return elem.get(key)
    else:
        return getattr(elem, key)


def list_pull(alist, key):
    return list(map(lambda elem: get_prop_or_key(elem, key), alist))


def get_multiprocessing_context():
    # Set execution method to spawn, to avoid fork and to have same behavior between platforms.
    # Older versions are stuck with whatever is the default on their platform (fork on
    # Unix-like and spawn on windows)
    #
    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.get_context
    if hasattr(multiprocessing, 'get_context'):
        return multiprocessing.get_context('spawn')
    else:
        return multiprocessing


def all_none(kwargs):
    for value in kwargs.values():
        if value is not None:
            return False
    return True


def check_script(path, return_code=0):
    try:
        subprocess.check_output(['python', path])
    except subprocess.CalledProcessError as exc:
        if return_code != 0:
            if exc.returncode == return_code:
                return
        raise


def check_cli_execute_file_pipeline(path, pipeline_fn_name, env_file=None):
    cli_cmd = ['python', '-m', 'dagster', 'pipeline', 'execute', '-f', path, '-n', pipeline_fn_name]

    if env_file:
        cli_cmd.append('-e')
        cli_cmd.append(env_file)

    try:
        subprocess.check_output(cli_cmd)
    except subprocess.CalledProcessError as cpe:
        print(cpe)
        raise cpe


@contextlib.contextmanager
def safe_tempfile_path():
    # This gets a valid temporary file path in the safest possible way, although there is still no
    # guarantee that another process will not create a file at this path. The NamedTemporaryFile is
    # deleted when the context manager exits and the file object is closed.
    #
    # This is preferable to using NamedTemporaryFile as a context manager and passing the name
    # attribute of the file object around because NamedTemporaryFiles cannot be opened a second time
    # if already open on Windows NT or later:
    # https://docs.python.org/3.8/library/tempfile.html#tempfile.NamedTemporaryFile
    # https://github.com/dagster-io/dagster/issues/1582
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        yield Path(path).as_posix()

    finally:
        if os.path.exists(path):
            os.unlink(path)


def ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


def ensure_dir(file_path):
    try:
        os.makedirs(file_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def ensure_file(path):
    ensure_dir(os.path.dirname(path))
    if not os.path.exists(path):
        touch_file(path)


def touch_file(path):
    ensure_dir(os.path.dirname(path))
    with open(path, 'a'):
        os.utime(path, None)


def _kill_on_event(termination_event):
    termination_event.wait()
    if IS_WINDOWS:
        # This will raise a KeyboardInterrupt in python land - meaning this wont be able to
        # interrupt things like sleep()
        thread.interrupt_main()
    else:
        # If on unix send an os level signal to interrupt any situation we may be stuck in
        os.kill(os.getpid(), signal.SIGINT)


# Function to be invoked by daemon thread in processes which seek to be cancellable.
# The motivation for this approach is to be able to exit cleanly on Windows. An alternative
# path is to change how the processes are opened and send CTRL_BREAK signals, which at
# the time of authoring seemed a more costly approach.
#
# Reading for the curious:
#  * https://stackoverflow.com/questions/35772001/how-to-handle-the-signal-in-python-on-windows-machine
#  * https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/
def start_termination_thread(termination_event):
    check.inst_param(
        termination_event, 'termination_event', ttype=type(get_multiprocessing_context().Event())
    )

    int_thread = threading.Thread(target=_kill_on_event, args=(termination_event,))
    int_thread.daemon = True
    int_thread.start()


def datetime_as_float(dt):
    check.inst_param(dt, 'dt', datetime.datetime)
    return float((dt - EPOCH).total_seconds())


# hashable frozen string to string dict
class frozentags(frozendict):
    def __init__(self, *args, **kwargs):
        super(frozentags, self).__init__(*args, **kwargs)
        check.dict_param(self, 'self', key_type=str, value_type=str)

    def __hash__(self):
        return hash(tuple(sorted(self.items())))

    def updated_with(self, new_tags):
        check.dict_param(new_tags, 'new_tags', key_type=str, value_type=str)
        updated = dict(self)
        for key, value in new_tags.items():
            updated[key] = value

        return frozentags(updated)


class EventGenerationManager(object):
    ''' Utility class that wraps an event generator function, that also yields a single instance of
    a typed object.  All events yielded before the typed object are yielded through the method
    `generate_setup_events` and all events yielded after the typed object are yielded through the
    method `generate_teardown_events`.

    This is used to help replace the context managers used in pipeline initialization with
    generators so that we can begin emitting initialization events AND construct a pipeline context
    object, while managing explicit setup/teardown.

    This does require calling `generate_setup_events` AND `generate_teardown_events` in order to
    get the typed object.
    '''

    def __init__(self, generator, object_cls, require_object=True):
        self.generator = check.generator(generator)
        self.object_cls = check.type_param(object_cls, 'object_cls')
        self.require_object = check.bool_param(require_object, 'require_object')
        self.object = None
        self.did_setup = False
        self.did_teardown = False

    def generate_setup_events(self):
        self.did_setup = True
        try:
            while self.object is None:
                obj = next(self.generator)
                if isinstance(obj, self.object_cls):
                    self.object = obj
                else:
                    yield obj
        except StopIteration:
            if self.require_object:
                check.inst_param(
                    self.object,
                    'self.object',
                    self.object_cls,
                    'generator never yielded object of type {}'.format(self.object_cls.__name__),
                )

    def get_object(self):
        if not self.did_setup:
            check.failed('Called `get_object` before `generate_setup_events`')
        return self.object

    def generate_teardown_events(self):
        self.did_teardown = True
        if self.object:
            for event in self.generator:
                yield event


def utc_datetime_from_timestamp(timestamp):
    tz = None
    if sys.version_info.major >= 3 and sys.version_info.minor >= 2:
        from datetime import timezone

        tz = timezone.utc
    else:
        import pytz

        tz = pytz.utc

    return datetime.datetime.fromtimestamp(timestamp, tz=tz)

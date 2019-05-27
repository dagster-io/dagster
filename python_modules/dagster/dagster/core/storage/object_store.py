import logging
import os
import shutil

from abc import ABCMeta, abstractmethod

import six

from dagster import check
from dagster.core.types.marshal import SerializationStrategy
from dagster.utils import mkdir_p


class ObjectStore(six.with_metaclass(ABCMeta)):
    def __init__(self, sep):
        # This is / for S3, os.sep for filesystem
        self.sep = check.str_param(sep, 'sep')

    @abstractmethod
    def set_object(self, key, obj, serialization_strategy=None):
        pass

    @abstractmethod
    def get_object(self, key, serialization_strategy=None):
        pass

    @abstractmethod
    def has_object(self, key):
        pass

    @abstractmethod
    def rm_object(self, key):
        pass

    @abstractmethod
    def cp_object(self, src, dst):
        pass

    @abstractmethod
    def uri_for_key(self, key, protocol=None):
        pass

    def key_for_paths(self, paths):
        return self.sep.join(paths)


class FileSystemObjectStore(ObjectStore):  # pylint: disable=no-init
    def __init__(self):
        super(FileSystemObjectStore, self).__init__(sep=os.sep)

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, 'key')
        # cannot check obj since could be arbitrary Python object
        check.opt_inst_param(
            serialization_strategy, 'serialization_strategy', SerializationStrategy
        )

        if os.path.exists(key):
            logging.warning('Removing existing path {path}'.format(path=key))
            os.unlink(key)

        # Ensure path exists
        mkdir_p(os.path.dirname(key))

        if serialization_strategy:
            serialization_strategy.serialize_to_file(obj, key)
        else:
            with open(key, 'wb') as f:
                f.write(obj)

        return key

    def get_object(self, key, serialization_strategy=None):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        if serialization_strategy:
            return serialization_strategy.deserialize_from_file(key)
        else:
            with open(key, 'rb') as f:
                return f.read()

    def has_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        return os.path.exists(key)

    def rm_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        if not self.has_object(key):
            return
        if os.path.isfile(key):
            os.unlink(key)
        elif os.path.isdir(key):
            shutil.rmtree(key)

    def cp_object(self, src, dst):
        check.invariant(not os.path.exists(dst), 'Path already exists {}'.format(dst))

        # Ensure output path exists
        mkdir_p(os.path.dirname(dst))

        if os.path.isfile(src):
            shutil.copy(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            check.failed('should not get here')

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, 'key')
        protocol = check.opt_str_param(protocol, 'protocol', default='file://')
        return protocol + '/' + key

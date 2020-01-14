import logging
import os
import shutil
from abc import ABCMeta, abstractmethod

import six

from dagster import check
from dagster.core.definitions.events import ObjectStoreOperation, ObjectStoreOperationType
from dagster.core.types.marshal import PickleSerializationStrategy, SerializationStrategy
from dagster.utils import mkdir_p


class ObjectStore(six.with_metaclass(ABCMeta)):
    def __init__(self, name, sep):
        '''Create an ObjectStore.
        
        Args:
            name (str) -- The user-visible name of the object store.
            sep (str) -- The path separator specific to the object store. On S3, this should be
                '/'; on the filesystem, `os.sep`.
        '''
        self.name = check.str_param(name, 'name')
        self.sep = check.str_param(sep, 'sep')

    @abstractmethod
    def set_object(self, key, obj, serialization_strategy=None):
        '''Implement this method to set an object in the object store.
        
        Should return an ObjectStoreOperation with op==ObjectStoreOperationType.SET_OBJECT
        on success.'''

    @abstractmethod
    def get_object(self, key, serialization_strategy=None):
        '''Implement this method to get an object from the object store.
        
        Should return an ObjectStoreOperation with op==ObjectStoreOperationType.GET_OBJECT
        on success.'''

    @abstractmethod
    def has_object(self, key):
        '''Implement this method to check if an object exists in the object store.
        
        Should return a boolean.'''

    @abstractmethod
    def rm_object(self, key):
        '''Implement this method to remove an object from the object store.
        
        Should return an ObjectStoreOperation with op==ObjectStoreOperationType.RM_OBJECT
        on success.'''

    @abstractmethod
    def cp_object(self, src, dst):
        '''Implement this method to copy an object from one key to another in the object store.
        
        Should return an ObjectStoreOperation with op==ObjectStoreOperationType.CP_OBJECT
        on success.'''

    @abstractmethod
    def uri_for_key(self, key, protocol=None):
        '''Implement this method to get a URI for a key in the object store.
        
        Should return a URI as a string.'''

    def key_for_paths(self, path_fragments):
        '''Joins path fragments into a key using the object-store specific path separator.'''
        return self.sep.join(path_fragments)


DEFAULT_SERIALIZATION_STRATEGY = PickleSerializationStrategy()


class FilesystemObjectStore(ObjectStore):  # pylint: disable=no-init
    def __init__(self):
        super(FilesystemObjectStore, self).__init__(name='filesystem', sep=os.sep)

    def set_object(self, key, obj, serialization_strategy=DEFAULT_SERIALIZATION_STRATEGY):
        check.str_param(key, 'key')
        # obj is an arbitrary Python object
        check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)

        if os.path.exists(key):
            logging.warning('Removing existing path {path}'.format(path=key))
            os.unlink(key)

        # Ensure path exists
        mkdir_p(os.path.dirname(key))

        serialization_strategy.serialize_to_file(obj, key)

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.SET_OBJECT,
            key=key,
            dest_key=None,
            obj=obj,
            serialization_strategy_name=serialization_strategy.name,
            object_store_name=self.name,
        )

    def get_object(self, key, serialization_strategy=DEFAULT_SERIALIZATION_STRATEGY):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')
        check.inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)

        obj = serialization_strategy.deserialize_from_file(key)

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.GET_OBJECT,
            key=key,
            dest_key=None,
            obj=obj,
            serialization_strategy_name=serialization_strategy.name,
            object_store_name=self.name,
        )

    def has_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        return os.path.exists(key)

    def rm_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        if self.has_object(key):
            if os.path.isfile(key):
                os.unlink(key)
            elif os.path.isdir(key):
                shutil.rmtree(key)

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.RM_OBJECT,
            key=key,
            dest_key=None,
            obj=None,
            serialization_strategy_name=None,
            object_store_name=self.name,
        )

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

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.CP_OBJECT,
            key=src,
            dest_key=dst,
            obj=None,
            serialization_strategy_name=None,
            object_store_name=self.name,
        )

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, 'key')
        protocol = check.opt_str_param(protocol, 'protocol', default='file://')
        return protocol + '/' + key

    def key_for_paths(self, path_fragments):
        '''Joins path fragments into a key using the object-store specific path separator.'''
        return os.path.join(*path_fragments)

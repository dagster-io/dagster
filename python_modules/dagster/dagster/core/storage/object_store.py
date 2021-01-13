import logging
import os
import shutil
from abc import ABC, abstractmethod

from dagster import check
from dagster.core.types.marshal import PickleSerializationStrategy, SerializationStrategy
from dagster.utils import mkdir_p


class ObjectStore(ABC):
    def __init__(self, name, sep="/"):
        """Create an ObjectStore.

        Args:
            name (str) -- The user-visible name of the object store.
            sep (Optional[str]) -- The path separator specific to the object store. On S3, this should be
                '/'; on the filesystem, `os.sep`.
        """
        self.name = check.str_param(name, "name")
        self.sep = check.opt_str_param(sep, "sep")

    @abstractmethod
    def set_object(self, key, obj, serialization_strategy=None):
        """Implement this method to set an object in the object store.

        Returns:
            str: The fully qualified key that the object was written to.
        """

    @abstractmethod
    def get_object(self, key, serialization_strategy=None):
        """Implement this method to get an object from the object store.

        Returns:
            Tuple[Any, str]: The object and the fully qualified key it was gotten from.
        """

    @abstractmethod
    def has_object(self, key):
        """Implement this method to check if an object exists in the object store.

        Should return a boolean."""

    @abstractmethod
    def rm_object(self, key):
        """Implement this method to remove an object from the object store.

        Returns:
            str: The fully qualified key that was removed.
        """

    @abstractmethod
    def cp_object(self, src, dst):
        """Implement this method to copy an object from one key to another in the object store.

        Returns:
            Tuple[str, str]: The fully qualified key of the source object and the fully qualified
                destination key.
        """

    @abstractmethod
    def uri_for_key(self, key, protocol=None):
        """Implement this method to get a URI for a key in the object store.

        Should return a URI as a string."""

    def key_for_paths(self, path_fragments):
        """Joins path fragments into a key using the object-store specific path separator."""
        return self.sep.join(path_fragments)


DEFAULT_SERIALIZATION_STRATEGY = PickleSerializationStrategy()


class InMemoryObjectStore(ObjectStore):
    def __init__(self):
        self.values = {}
        super(InMemoryObjectStore, self).__init__(name="memory")

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, "key")
        self.values[key] = obj
        return key

    def get_object(self, key, serialization_strategy=DEFAULT_SERIALIZATION_STRATEGY):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        obj = self.values[key]
        return obj, key

    def has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        return key in self.values

    def rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        if self.has_object(key):
            self.values.pop(key)

        return key

    def cp_object(self, src, dst):
        check.invariant(not dst in self.values, "key {} already in use".format(dst))
        check.invariant(src in self.values, "key {} not present".format(src))
        self.values[dst] = self.values[src]
        return src, dst

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, "key")
        return key


class FilesystemObjectStore(ObjectStore):  # pylint: disable=no-init
    def __init__(self):
        super(FilesystemObjectStore, self).__init__(name="filesystem", sep=os.sep)

    def set_object(self, key, obj, serialization_strategy=DEFAULT_SERIALIZATION_STRATEGY):
        check.str_param(key, "key")
        # obj is an arbitrary Python object
        check.inst_param(serialization_strategy, "serialization_strategy", SerializationStrategy)

        if os.path.exists(key):
            logging.warning("Removing existing path {path}".format(path=key))
            os.unlink(key)

        # Ensure path exists
        mkdir_p(os.path.dirname(key))

        serialization_strategy.serialize_to_file(obj, key)

        return key

    def get_object(self, key, serialization_strategy=DEFAULT_SERIALIZATION_STRATEGY):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        check.inst_param(serialization_strategy, "serialization_strategy", SerializationStrategy)

        return serialization_strategy.deserialize_from_file(key), key

    def has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        return os.path.exists(key)

    def rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        if self.has_object(key):
            if os.path.isfile(key):
                os.unlink(key)
            elif os.path.isdir(key):
                shutil.rmtree(key)

        return key

    def cp_object(self, src, dst):
        check.invariant(not os.path.exists(dst), "Path already exists {}".format(dst))

        # Ensure output path exists
        mkdir_p(os.path.dirname(dst))
        if os.path.isfile(src):
            shutil.copy(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            check.failed("should not get here")

        return src, dst

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, "key")
        protocol = check.opt_str_param(protocol, "protocol", default="file://")
        return protocol + "/" + key

    def key_for_paths(self, path_fragments):
        """Joins path fragments into a key using the object-store specific path separator."""
        return os.path.join(*path_fragments)

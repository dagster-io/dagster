from abc import ABCMeta, abstractmethod

import six


class Lakehouse(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def hydrate(self, context, table_type, table_metadata, table_handle, dest_table_metadata):
        pass

    @abstractmethod
    def materialize(self, context, table_type, table_metadata, value):
        pass

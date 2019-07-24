import os

from collections import namedtuple
from enum import Enum

from dagster import check

from .utils import DEFAULT_OUTPUT


def last_file_comp(path):
    return os.path.basename(os.path.normpath(path))


class EventMetadataEntry(namedtuple('_EventMetadataEntry', 'label description entry_data')):
    '''A structure for describing metadata for Dagster events.

    Args:
        label (str):
        description (Optional[str]):
        entry_data (List[EntryDataUnion]):
            A list of typed metadata entries. The different types allow for customized display in
            tools like dagit.

    '''

    def __new__(cls, label, description, entry_data):
        return super(EventMetadataEntry, cls).__new__(
            cls,
            check.str_param(label, 'label'),
            check.opt_str_param(description, 'description'),
            check.inst_param(entry_data, 'entry_data', EntryDataUnion),
        )

    @staticmethod
    def text(text, label, description=None):
        'A EventMetadataEntry with a single TextMetadataEntryData entry'
        return EventMetadataEntry(label, description, TextMetadataEntryData(text))

    @staticmethod
    def url(url, label, description=None):
        'A EventMetadataEntry with a single UrlMetadataEntryData entry'
        return EventMetadataEntry(label, description, UrlMetadataEntryData(url))

    @staticmethod
    def path(path, label, description=None):
        'A EventMetadataEntry with a single PathMetadataEntryData entry'
        return EventMetadataEntry(label, description, PathMetadataEntryData(path))

    @staticmethod
    def fspath(path, label=None, description=None):
        'Just like path, but makes label last path component if None'
        return EventMetadataEntry.path(
            path, label if label is not None else last_file_comp(path), description
        )

    @staticmethod
    def json(data, label, description=None):
        return EventMetadataEntry(label, description, JsonMetadataEntryData(data))


class TextMetadataEntryData(namedtuple('_TextMetadataEntryData', 'text')):
    def __new__(cls, text):
        return super(TextMetadataEntryData, cls).__new__(cls, check.str_param(text, 'text'))


class UrlMetadataEntryData(namedtuple('_UrlMetadataEntryData', 'url')):
    def __new__(cls, url):
        return super(UrlMetadataEntryData, cls).__new__(cls, check.str_param(url, 'url'))


class PathMetadataEntryData(namedtuple('_PathMetadataEntryData', 'path')):
    def __new__(cls, path):
        return super(PathMetadataEntryData, cls).__new__(cls, check.str_param(path, 'path'))


class JsonMetadataEntryData(namedtuple('_JsonMetadataEntryData', 'data')):
    def __new__(cls, data):
        return super(JsonMetadataEntryData, cls).__new__(
            cls, check.dict_param(data, 'data', key_type=str)
        )


EntryDataUnion = (
    TextMetadataEntryData,
    UrlMetadataEntryData,
    PathMetadataEntryData,
    JsonMetadataEntryData,
)


class Output(namedtuple('_Result', 'value output_name')):
    '''A value produced by a solid compute function for downstream consumption. An implementer
    of a SolidDefinition directly must provide a compute function that yields objects of this type.

    Args:
        value (Any): Value returned by the compute function.
        output_name (str): Name of the output returns. Defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Output, cls).__new__(cls, value, check.str_param(output_name, 'output_name'))


class Materialization(namedtuple('_Materialization', 'label description metadata_entries')):
    '''A value materialized by a solid compute function.

    As opposed to Outputs, Materializations can not be passed to other solids and persistence
    is not controlled by dagster. They are a useful way to communicate side effects to the system
    and display them to the end user.

    Args:
        label (str): A short display name for the materialized value.
        description (Optional[str]): A longer description of the materialized value.
        metadata_entries (Optional[List[EventMetadataEntry]]):
            Arbitrary metadata about the materialized value.
    '''

    @staticmethod
    def file(path, description=None):
        return Materialization(
            label=last_file_comp(path),
            description=description,
            metadata_entries=[EventMetadataEntry.fspath(path)],
        )

    def __new__(cls, label, description=None, metadata_entries=None):
        return super(Materialization, cls).__new__(
            cls,
            label=check.str_param(label, 'label'),
            description=check.opt_str_param(description, 'description'),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


class ExpectationResult(
    namedtuple('_ExpectationResult', 'success label description metadata_entries')
):
    '''The result of a data quality test.

    ExpectationResults can be yielded from solids just like Outputs and Materializations.

    Args:
        success (bool): Whether the expectation passed or not.
        label (Optional[str]): Short display name for expectation. Defaults to "result".
        description (Optional[str]): A longer description of the data quality test.
        metadata_entries (Optional[List[EventMetadataEntry]]):
            Arbitrary metadata about the expectation.
    '''

    def __new__(cls, success, label=None, description=None, metadata_entries=None):
        return super(ExpectationResult, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            label=check.opt_str_param(label, 'label', 'result'),
            description=check.opt_str_param(description, 'description'),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


class TypeCheck(namedtuple('_TypeCheck', 'description metadata_entries')):
    '''Used to communicate metadata about a value as it is evaluated against
    a declared expected type.
    '''

    def __new__(cls, description=None, metadata_entries=None):
        return super(TypeCheck, cls).__new__(
            cls,
            description=check.opt_str_param(description, 'description'),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


class Failure(Exception):
    '''Can be raised from a solid compute function to return structured metadata
    about the failure.
    '''

    def __init__(self, description=None, metadata_entries=None):
        super(Failure, self).__init__(description)
        self.description = check.opt_str_param(description, 'description')
        self.metadata_entries = check.opt_list_param(
            metadata_entries, 'metadata_entries', of_type=EventMetadataEntry
        )


class ObjectStoreOperationType(Enum):
    SET_OBJECT = 'SET_OBJECT'
    GET_OBJECT = 'GET_OBJECT'
    RM_OBJECT = 'RM_OBJECT'
    CP_OBJECT = 'CP_OBJECT'


class ObjectStoreOperation(
    namedtuple(
        '_ObjectStoreOperation',
        'op key dest_key obj serialization_strategy_name object_store_name value_name',
    )
):
    '''Used internally by Dagster machinery when values are written to and read from an
    ObjectStore.
    
    Args:
        op (ObjectStoreOperationType): The type of the operation on the object store.
        key (str): The key of the object on which the operation was performed.
        dest_key (Optional[str]): The destination key, if any, to which the object was copied.
        obj (Any): The object, if any, retrieved by the operation.
        serialization_strategy_name (Optional[str]): The name of the serialization strategy, if any,
            employed by the operation
        object_store_name (Optional[str]): The name of the object store that performed the
            operation.
    '''

    def __new__(
        cls,
        op,
        key,
        dest_key=None,
        obj=None,
        serialization_strategy_name=None,
        object_store_name=None,
        value_name=None,
    ):
        return super(ObjectStoreOperation, cls).__new__(
            cls,
            op=op,
            key=check.str_param(key, 'key'),
            dest_key=check.opt_str_param(dest_key, 'dest_key'),
            obj=obj,
            serialization_strategy_name=check.opt_str_param(
                serialization_strategy_name, 'serialization_strategy_name'
            ),
            object_store_name=check.opt_str_param(object_store_name, 'object_store_name'),
            value_name=check.opt_str_param(value_name, 'value_name'),
        )

    @classmethod
    def serializable(cls, inst, **kwargs):
        return cls(
            **dict(
                {
                    'op': inst.op.value,
                    'key': inst.key,
                    'dest_key': inst.dest_key,
                    'obj': None,
                    'serialization_strategy_name': inst.serialization_strategy_name,
                    'object_store_name': inst.object_store_name,
                },
                **kwargs
            )
        )

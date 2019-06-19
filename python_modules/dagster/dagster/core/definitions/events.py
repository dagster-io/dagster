import os
from collections import namedtuple

from dagster import check

from .utils import DEFAULT_OUTPUT


class EventMetadataEntry(namedtuple('_EventMetadataEntry', 'label description entry_data')):
    def __new__(cls, label, description, entry_data):
        return super(EventMetadataEntry, cls).__new__(
            cls,
            check.str_param(label, 'label'),
            check.opt_str_param(description, 'description'),
            check.inst_param(entry_data, 'entry_data', EntryDataUnion),
        )

    @staticmethod
    def text(text, label, description=None):
        return EventMetadataEntry(label, description, TextMetadataEntryData(text))

    @staticmethod
    def url(url, label, description=None):
        return EventMetadataEntry(label, description, UrlMetadataEntryData(url))

    @staticmethod
    def path(path, label, description=None):
        return EventMetadataEntry(label, description, PathMetadataEntryData(path))

    @staticmethod
    def fspath(path, label=None, description=None):
        'Just like path, but makes label last path component if None'
        return EventMetadataEntry.path(
            path,
            label if label is not None else os.path.basename(os.path.normpath(path)),
            description,
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


class Result(namedtuple('_Result', 'value output_name')):
    '''A solid compute function return a stream of Result objects.
    An implementator of a SolidDefinition must provide a compute that
    yields objects of this type.

    Attributes:
        value (Any): Value returned by the transform.
        output_name (str): Name of the output returns. defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(cls, value, check.str_param(output_name, 'output_name'))


class Materialization(namedtuple('_Materialization', 'label description metadata_entries')):
    '''A value materialized by an execution step.

    As opposed to Results, Materializations can not be passed to other solids and persistence
    is not controlled by dagster. They are a useful way to communicate side effects to the system
    and display them to the end user.

    Attributes:
        path (str): The path to the materialized value.
        name (str): A short display name for the materialized value.
        description (str): A longer description of the materialized value.
        result_metadata (dict): Arbitrary metadata about the materialized value.
    '''

    @staticmethod
    def legacy_ctor(path, name=None, description=None, result_metadata=None):
        '''The constructor for this object used to have this signature. Introduced
        this temporary static method that matched that signature to make migration
        easier and the initial diff less thrashy -- schrockn (06/17/19)'''
        check.str_param(path, 'path')
        path_entry = EventMetadataEntry.path(label='a_path', path=path)
        return Materialization(
            label=name if name else 'unlabeled',
            description=description,
            metadata_entries=[
                path_entry,
                EventMetadataEntry.json(label='json', data=result_metadata),
            ]
            if result_metadata
            else [path_entry],
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
    ''' Result of an expectation callback.

    When Expectations are evaluated in the callback passed to ExpectationDefinitions,
    the user must return an ExpectationResult object from the callback.

    Attributes:

        success (bool): Whether the expectation passed or not.
        name (str): Short display name for expectation
        message (str): Information about the computation. Typically only used in the failure case.
        result_metadata (dict): Arbitrary information about the expectation result.
    '''

    @staticmethod
    def legacy_ctor(success, name=None, message=None, result_metadata=None):
        '''The constructor for this object used to have this signature. Introduced
        this temporary static method that matched that signature to make migration
        easier and the initial diff less thrashy -- schrockn (06/17/19)'''
        return ExpectationResult(
            success=success,
            label=name if name is not None else 'unlabeled',
            description=message,
            metadata_entries=[]
            if result_metadata is None
            else [EventMetadataEntry.json(label='json', data=result_metadata)],
        )

    def __new__(cls, success, label, description=None, metadata_entries=None):
        return super(ExpectationResult, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            label=check.str_param(label, 'label'),
            description=check.opt_str_param(description, 'description'),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )

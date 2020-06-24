import os
import re
from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.errors import DagsterInvalidAssetKey
from dagster.serdes import whitelist_for_serdes

from .utils import DEFAULT_OUTPUT


def last_file_comp(path):
    return os.path.basename(os.path.normpath(path))


ASSET_KEY_REGEX = re.compile('^[a-zA-Z0-9_]+$')  # alphanumeric, _, -, .
ASSET_KEY_SPLIT_REGEX = re.compile('[^a-zA-Z0-9_]')
ASSET_KEY_STRUCTURED_DELIMITER = '.'


def validate_asset_key_string(s):
    if not s or not ASSET_KEY_REGEX.match(s):
        raise DagsterInvalidAssetKey()

    return s


def parse_asset_key_string(s):
    return list(filter(lambda x: x, re.split(ASSET_KEY_SPLIT_REGEX, s)))


def validate_structured_asset_key(l):
    if len(l) == 0:
        raise DagsterInvalidAssetKey()

    for s in l:
        validate_asset_key_string(s)

    return l


@whitelist_for_serdes
class AssetKey(namedtuple('_AssetKey', 'path')):
    ''' Object representing the structure of an asset key.  Takes in a sanitized string or list of
    strings.

    Example usage:

        AssetKey('flat_asset_key')

        AssetKey(['parent', 'child', 'grandchild'])

    Args:
        asset_key_str_or_list (str|str[]): String or list of strings.  A list of strings represent
            the hierarchical structure of the asset_key.
    '''

    def __new__(cls, path=None):
        if check.is_str(path):
            path = [validate_asset_key_string(path)]
        else:
            path = validate_structured_asset_key(
                check.list_param(path, 'asset_key_str_or_list', of_type=str)
            )

        return super(AssetKey, cls).__new__(cls, path=path)

    def __str__(self):
        return 'AssetKey({})'.format(self.to_string())

    def __repr__(self):
        return 'AssetKey({})'.format(self.to_string())

    def __hash__(self):
        return hash(tuple(self.path))

    def __eq__(self, other):
        if not isinstance(other, AssetKey):
            return False
        return self.to_string() == other.to_string()

    def to_string(self):
        if not self.path:
            return None
        return ASSET_KEY_STRUCTURED_DELIMITER.join(self.path)

    @staticmethod
    def from_db_string(asset_key_string):
        if not asset_key_string:
            return None
        return AssetKey(parse_asset_key_string(asset_key_string))

    @staticmethod
    def from_graphql_input(asset_key):
        if asset_key and asset_key.get('path'):
            return AssetKey(asset_key.get('path'))
        return None


@whitelist_for_serdes
class EventMetadataEntry(namedtuple('_EventMetadataEntry', 'label description entry_data')):
    '''The standard structure for describing metadata for Dagster events.

    Lists of objects of this type can be passed as arguments to Dagster events and will be displayed
    in Dagit and other tooling.

    Args:
        label (str): Short display label for this metadata entry.
        description (Optional[str]): A human-readable description of this metadata entry.
        entry_data (Union[TextMetadataEntryData, UrlMetadataEntryData, PathMetadataEntryData, JsonMetadataEntryData, MarkdownMetadataEntryData]):
            Typed metadata entry data. The different types allow for customized display in tools
            like dagit.
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
        '''Static constructor for a metadata entry containing text as
        :py:class:`TextMetadataEntryData`.

        Args:
            text (str): The text of this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        '''
        return EventMetadataEntry(label, description, TextMetadataEntryData(text))

    @staticmethod
    def url(url, label, description=None):
        '''Static constructor for a metadata entry containing a URL as
        :py:class:`UrlMetadataEntryData`.

        Args:
            url (str): The URL contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        '''
        return EventMetadataEntry(label, description, UrlMetadataEntryData(url))

    @staticmethod
    def path(path, label, description=None):
        '''Static constructor for a metadata entry containing a path as
        :py:class:`PathMetadataEntryData`.

        Args:
            path (str): The path contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        '''
        return EventMetadataEntry(label, description, PathMetadataEntryData(path))

    @staticmethod
    def fspath(path, label=None, description=None):
        '''Static constructor for a metadata entry containing a filesystem path as
        :py:class:`PathMetadataEntryData`.

        Args:
            path (str): The path contained by this metadata entry.
            label (Optional[str]): Short display label for this metadata entry. Defaults to the
                base name of the path.
            description (Optional[str]): A human-readable description of this metadata entry.
        '''
        return EventMetadataEntry.path(
            path, label if label is not None else last_file_comp(path), description
        )

    @staticmethod
    def json(data, label, description=None):
        '''Static constructor for a metadata entry containing JSON data as
        :py:class:`JsonMetadataEntryData`.

        Args:
            data (Dict[str, Any]): The JSON data contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        '''
        return EventMetadataEntry(label, description, JsonMetadataEntryData(data))

    @staticmethod
    def md(md_str, label, description=None):
        '''Static constructor for a metadata entry containing markdown.

        Args:
            md_str (str): The markdown contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        '''
        return EventMetadataEntry(label, description, MarkdownMetadataEntryData(md_str))

    @staticmethod
    def python_artifact(python_artifact, label, description=None):
        check.callable_param(python_artifact, 'python_artifact')
        return EventMetadataEntry(
            label,
            description,
            PythonArtifactMetadataEntryData(python_artifact.__module__, python_artifact.__name__),
        )

    @staticmethod
    def float(value, label, description=None):
        check.float_param(value, 'value')
        return EventMetadataEntry(label, description, FloatMetadataEntryData(value),)


@whitelist_for_serdes
class TextMetadataEntryData(namedtuple('_TextMetadataEntryData', 'text')):
    '''Container class for text metadata entry data.

    Args:
        text (str): The text data.
    '''

    def __new__(cls, text):
        return super(TextMetadataEntryData, cls).__new__(cls, check.str_param(text, 'text'))


@whitelist_for_serdes
class UrlMetadataEntryData(namedtuple('_UrlMetadataEntryData', 'url')):
    '''Container class for URL metadata entry data.

    Args:
        url (str): The URL as a string.
    '''

    def __new__(cls, url):
        return super(UrlMetadataEntryData, cls).__new__(cls, check.str_param(url, 'url'))


@whitelist_for_serdes
class PathMetadataEntryData(namedtuple('_PathMetadataEntryData', 'path')):
    '''Container class for path metadata entry data.

    Args:
        path (str): The path as a string.
    '''

    def __new__(cls, path):
        return super(PathMetadataEntryData, cls).__new__(cls, check.str_param(path, 'path'))


@whitelist_for_serdes
class JsonMetadataEntryData(namedtuple('_JsonMetadataEntryData', 'data')):
    '''Container class for JSON metadata entry data.

    Args:
        data (Dict[str, Any]): The JSON data.
    '''

    def __new__(cls, data):
        return super(JsonMetadataEntryData, cls).__new__(
            cls, check.dict_param(data, 'data', key_type=str)
        )


@whitelist_for_serdes
class MarkdownMetadataEntryData(namedtuple('_MarkdownMetadataEntryData', 'md_str')):
    '''Container class for markdown metadata entry data.

    Args:
        md_str (str): The markdown as a string.
    '''

    def __new__(cls, md_str):
        return super(MarkdownMetadataEntryData, cls).__new__(cls, check.str_param(md_str, 'md_str'))


@whitelist_for_serdes
class PythonArtifactMetadataEntryData(
    namedtuple('_PythonArtifactMetadataEntryData', 'module name')
):
    def __new__(cls, module, name):
        return super(PythonArtifactMetadataEntryData, cls).__new__(
            cls, check.str_param(module, 'module'), check.str_param(name, 'name')
        )


@whitelist_for_serdes
class FloatMetadataEntryData(namedtuple('_FloatMetadataEntryData', 'value')):
    def __new__(cls, value):
        check.float_param(value, 'value')
        return super(FloatMetadataEntryData, cls).__new__(cls, check.float_param(value, 'value'))


EntryDataUnion = (
    TextMetadataEntryData,
    UrlMetadataEntryData,
    PathMetadataEntryData,
    JsonMetadataEntryData,
    MarkdownMetadataEntryData,
    PythonArtifactMetadataEntryData,
    FloatMetadataEntryData,
)


class Output(namedtuple('_Output', 'value output_name')):
    '''Event corresponding to one of a solid's outputs.

    Solid compute functions must explicitly yield events of this type when they have more than
    one output, or when they also yield events of other types, or when defining a solid using the
    :py:class:`SolidDefinition` API directly.

    Outputs are values produced by solids that will be consumed by downstream solids in a pipeline.
    They are type-checked at solid boundaries when their corresponding :py:class:`OutputDefinition`
    or the downstream :py:class:`InputDefinition` is typed.

    Args:
        value (Any): The value returned by the compute function.
        output_name (Optional[str]): Name of the corresponding output definition. (default:
            "result")
    '''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Output, cls).__new__(cls, value, check.str_param(output_name, 'output_name'))


@whitelist_for_serdes
class Materialization(
    namedtuple('_Materialization', 'label description metadata_entries asset_key')
):
    '''Event indicating that a solid has materialized a value.

    Solid compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that they have produced a materialized value as a
    side effect of computation. Unlike outputs, materializations can not be passed to other solids,
    and their persistence is controlled by solid logic, rather than by the Dagster framework.

    Solid authors should use these events to organize metadata about the side effects of their
    computations to enable downstream tooling like artifact catalogues and diff tools.

    Args:
        label (str): A short display name for the materialized value.
        description (Optional[str]): A longer human-radable description of the materialized value.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            materialized value.
        asset_key (Optional[str|AssetKey]): An optional parameter to identify the materialized asset
            across pipeline runs
    '''

    @staticmethod
    def file(path, description=None, asset_key=None):
        '''Static constructor for standard materializations corresponding to files on disk.

        Args:
            path (str): The path to the file.
            description (Optional[str]): A human-readable description of the materialization.
        '''
        return Materialization(
            label=last_file_comp(path),
            description=description,
            metadata_entries=[EventMetadataEntry.fspath(path)],
            asset_key=asset_key,
        )

    def __new__(cls, label=None, description=None, metadata_entries=None, asset_key=None):
        if asset_key and check.is_str(asset_key):
            asset_key = AssetKey(parse_asset_key_string(asset_key))
        else:
            check.opt_inst_param(asset_key, 'asset_key', AssetKey)

        if not label:
            check.param_invariant(
                asset_key and asset_key.path,
                'label',
                'Either label or asset_key with a path must be provided',
            )
            label = asset_key.to_string()

        return super(Materialization, cls).__new__(
            cls,
            label=check.str_param(label, 'label'),
            description=check.opt_str_param(description, 'description'),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
            asset_key=asset_key,
        )


@whitelist_for_serdes
class ExpectationResult(
    namedtuple('_ExpectationResult', 'success label description metadata_entries')
):
    '''Event corresponding to a data quality test.

    Solid compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that a data quality test has produced a (positive or
    negative) result.

    Args:
        success (bool): Whether the expectation passed or not.
        label (Optional[str]): Short display name for expectation. Defaults to "result".
        description (Optional[str]): A longer human-readable description of the expectation.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            expectation.
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


@whitelist_for_serdes
class TypeCheck(namedtuple('_TypeCheck', 'success description metadata_entries')):
    '''Event corresponding to a successful typecheck.

    Events of this type should be returned by user-defined type checks when they need to encapsulate
    additional metadata about a type check's success or failure. (i.e., when using
    :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type>`, or the underlying
    :py:func:`PythonObjectDagsterType` API.)

    Solid compute functions should generally avoid yielding events of this type to avoid confusion.

    Args:
        success (bool): ``True`` if the type check succeeded, ``False`` otherwise.
        description (Optional[str]): A human-readable description of the type check.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            type check.
    '''

    def __new__(cls, success, description=None, metadata_entries=None):
        return super(TypeCheck, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            description=check.opt_str_param(description, 'description'),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


class Failure(Exception):
    '''Event indicating solid failure.

    Raise events of this type from within solid compute functions or custom type checks in order to
    indicate an unrecoverable failure in user code to the Dagster machinery and return
    structured metadata about the failure.

    Args:
        description (Optional[str]): A human-readable description of the failure.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            failure.
    '''

    def __init__(self, description=None, metadata_entries=None):
        super(Failure, self).__init__(description)
        self.description = check.opt_str_param(description, 'description')
        self.metadata_entries = check.opt_list_param(
            metadata_entries, 'metadata_entries', of_type=EventMetadataEntry
        )


class RetryRequested(Exception):  # base exception instead?
    '''
    EXPERIMENTAL: A simple tool for retrying the execution of a step in dagster.

    Args:
        max_retries (Optional[int]):
            The max number of retries this step should attempt before failing
        seconds_to_wait (Optional[int]):
            Seconds to wait before restarting the step after putting the step in
            to the up_for_retry state
    '''

    def __init__(self, max_retries=1, seconds_to_wait=None):
        super(RetryRequested, self).__init__()
        self.max_retries = check.int_param(max_retries, 'max_retries')
        self.seconds_to_wait = check.opt_int_param(seconds_to_wait, 'seconds_to_wait')


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
    '''This event is used internally by Dagster machinery when values are written to and read from
    an ObjectStore.

    Users should not import this class or yield events of this type from user code.

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
                    'value_name': inst.value_name,
                },
                **kwargs
            )
        )

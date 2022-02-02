from collections import namedtuple
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
)

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterError, DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterType, resolve_dagster_type

from .inference import InferredOutputProps
from .input import NoValueSentinel
from .utils import DEFAULT_OUTPUT, check_valid_name

if TYPE_CHECKING:
    from dagster.core.definitions.partition import PartitionsDefinition

TOut = TypeVar("TOut", bound="OutputDefinition")
TAssetOut = TypeVar("TAssetOut", bound="AssetOutputDefinition")


class NoNameSentinel:
    pass


class OutputDefinition:
    """Defines an output from a solid's compute function.

    Solids can have multiple outputs, in which case outputs cannot be anonymous.

    Many solids have only one output, in which case the user can provide a single output definition
    that will be given the default name, "result".

    Output definitions may be typed using the Dagster type system.

    Args:
        dagster_type (Optional[Union[Type, DagsterType]]]): The type of this output.
            Users should provide the Python type of the objects that they expect the solid to yield
            for this output, or a :py:class:`DagsterType` that defines a runtime check that they
            want to be run on this output. Defaults to :py:class:`Any`.
        name (Optional[str]): Name of the output. (default: "result")
        description (Optional[str]): Human-readable description of the output.
        is_required (Optional[bool]): Whether the presence of this field is required. (default: True)
        io_manager_key (Optional[str]): The resource key of the IOManager used for storing this
            output and loading it in downstream steps (default: "io_manager").
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the output.
            For example, users can provide a file path if the data object will be stored in a
            filesystem, or provide information of a database table when it is going to load the data
            into the table.
    """

    def __init__(
        self,
        dagster_type=None,
        name=None,
        description=None,
        is_required=None,
        io_manager_key=None,
        metadata=None,
        # make sure new parameters are updated in combine_with_inferred below
    ):
        self._name = (
            check_valid_name(check.opt_str_param(name, "name", DEFAULT_OUTPUT))
            if name is not NoNameSentinel
            else None
        )
        self._type_not_set = dagster_type is None
        self._dagster_type = resolve_dagster_type(dagster_type)
        self._description = check.opt_str_param(description, "description")
        self._is_required = check.opt_bool_param(is_required, "is_required", default=True)
        self._manager_key = check.opt_str_param(
            io_manager_key, "io_manager_key", default="io_manager"
        )
        self._metadata = metadata

    @property
    def name(self):
        return self._name

    @property
    def dagster_type(self):
        return self._dagster_type

    @property
    def description(self):
        return self._description

    @property
    def optional(self):
        return not self._is_required

    @property
    def is_required(self):
        return self._is_required

    @property
    def io_manager_key(self):
        return self._manager_key

    @property
    def metadata(self):
        return self._metadata

    @property
    def is_dynamic(self):
        return False

    @property
    def is_asset(self):
        return False

    def mapping_from(self, solid_name, output_name=None):
        """Create an output mapping from an output of a child solid.

        In a CompositeSolidDefinition, you can use this helper function to construct
        an :py:class:`OutputMapping` from the output of a child solid.

        Args:
            solid_name (str): The name of the child solid from which to map this output.
            input_name (str): The name of the child solid's output from which to map this output.

        Examples:

            .. code-block:: python

                output_mapping = OutputDefinition(Int).mapping_from('child_solid')
        """
        return OutputMapping(self, OutputPointer(solid_name, output_name))

    @staticmethod
    def create_from_inferred(inferred: InferredOutputProps) -> "OutputDefinition":
        return OutputDefinition(
            dagster_type=_checked_inferred_type(inferred.annotation),
            description=inferred.description,
        )

    def to_out(self) -> "Out":
        return Out(
            dagster_type=self.dagster_type,
            description=self.description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
        )

    def combine_with_inferred(self: TOut, inferred: InferredOutputProps) -> TOut:
        dagster_type = self._dagster_type
        if self._type_not_set:
            dagster_type = _checked_inferred_type(inferred.annotation)
        if self._description is None:
            description = inferred.description
        else:
            description = self.description

        return self.__class__(
            name=self._name,
            dagster_type=dagster_type,
            description=description,
            is_required=self._is_required,
            io_manager_key=self._manager_key,
            metadata=self._metadata,
        )


class AssetOutputDefinition(OutputDefinition):
    """
    Variant of :py:class:`OutputDefinition <dagster.OutputDefinition>` for an output that will be
    used to generate a tracked asset at runtime.

    Args:
        asset_key (Union[AssetKey, str, Sequence[str]]): The AssetKey representing the asset that
            will be updated using the data associated with this output.
        dagster_type (Optional[Union[Type, DagsterType]]]):
            The type of this output. Should only be set if the correct type can not
            be inferred directly from the type signature of the decorated function.
        name (Optional[str]): Name of the output. (default: "result")
        description (Optional[str]): Human-readable description of the output.
        is_required (Optional[bool]): Whether the presence of this field is required. (default: True)
        io_manager_key (Optional[str]): The resource key of the output manager used for this output.
            (default: "io_manager").
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the output.
            For example, users can provide a file path if the data object will be stored in a
            filesystem, or provide information of a database table when it is going to load the data
            into the table.
        asset_partitions_fn (Optional[OutputContext -> Set[str]]): A function that produces a set of
            partitions from the OutputContext) which should be associated with this Out.
        asset_partitions_def (Optional[PartitionsDefinition]): Defines the entire set of partitions
            on the asset associated with this AssetOut.
        dependencies (Optional[Union[Set[AssetKey]]): The set of AssetKeys
            that this particular AssetOut depends on. If not included, this set will be inferred
            to be the set of AssetKeys attached to inputs of this AssetOut's Op.
    """

    def __init__(
        self,
        asset_key,
        dagster_type=None,
        name=None,
        description=None,
        is_required=None,
        io_manager_key=None,
        metadata=None,
        asset_partitions_fn=None,
        asset_partitions_def=None,
        dependencies=None,
    ):
        from dagster.core.definitions.partition import PartitionsDefinition

        super().__init__(
            dagster_type=dagster_type,
            name=name,
            description=description,
            is_required=is_required,
            io_manager_key=io_manager_key,
            metadata=metadata,
        )

        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        self._asset_partitions_fn = check.opt_callable_param(
            asset_partitions_fn, "asset_partitions_fn"
        )
        self._asset_partitions_def = check.opt_inst_param(
            asset_partitions_def, "asset_partition_def", PartitionsDefinition
        )
        check.opt_set_param(dependencies, "dependencies", AssetKey)
        self._dependencies = dependencies

    @property
    def is_asset(self):
        return True

    @property
    def asset_partitions_def(self):
        return self._asset_partitions_def

    @property
    def asset_key(self) -> AssetKey:
        return self._asset_key

    @property
    def dependencies(self) -> Optional[Set[AssetKey]]:
        return self._dependencies

    def get_asset_partitions(self, context) -> Optional[Set[str]]:
        """Get the set of partitions associated with this AssetOutputDefinition for the given
        :py:class:`OutputContext` (if any).

        Args:
            context (OutputContext): The OutputContext that this AssetOutputDefinition is being
                evaluated in
        """
        if self._asset_partitions_fn is None:
            return None

        return self._asset_partitions_fn(context)

    def to_out(self) -> "AssetOut":
        return AssetOut(
            dagster_type=self.dagster_type,
            description=self.description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
            asset_key=self.asset_key,
            asset_partitions_fn=self._asset_partitions_fn,
            asset_partitions_def=self.asset_partitions_def,
            dependencies=self.dependencies,
        )

    def combine_with_inferred(self: TAssetOut, inferred: InferredOutputProps) -> TAssetOut:
        dagster_type = self._dagster_type
        if self._type_not_set:
            dagster_type = _checked_inferred_type(inferred.annotation)
        if self._description is None:
            description = inferred.description
        else:
            description = self.description

        return self.__class__(
            name=self._name,
            dagster_type=dagster_type,
            description=description,
            is_required=self._is_required,
            io_manager_key=self._manager_key,
            metadata=self._metadata,
            asset_key=self._asset_key,
            asset_partitions_fn=self._asset_partitions_fn,
            asset_partitions_def=self.asset_partitions_def,
            dependencies=self.dependencies,
        )


def _checked_inferred_type(inferred: Any) -> DagsterType:
    try:
        return resolve_dagster_type(inferred)
    except DagsterError as e:
        raise DagsterInvalidDefinitionError(
            f"Problem using type '{inferred}' from return type annotation, correct the issue "
            "or explicitly set the dagster_type on your OutputDefinition."
        ) from e


class DynamicOutputDefinition(OutputDefinition):
    """
    Variant of :py:class:`OutputDefinition <dagster.OutputDefinition>` for an
    output that will dynamically alter the graph at runtime.

    When using in a composition function such as :py:func:`@pipeline <dagster.pipeline>`,
    dynamic outputs must be used with either

    * ``map`` - clone downstream solids for each separate :py:class:`DynamicOutput`
    * ``collect`` - gather across all :py:class:`DynamicOutput` in to a list

    Uses the same constructor as :py:class:`OutputDefinition <dagster.OutputDefinition>`

        .. code-block:: python

            @solid(
                config_schema={
                    "path": Field(str, default_value=file_relative_path(__file__, "sample"))
                },
                output_defs=[DynamicOutputDefinition(str)],
            )
            def files_in_directory(context):
                path = context.solid_config["path"]
                dirname, _, filenames = next(os.walk(path))
                for file in filenames:
                    yield DynamicOutput(os.path.join(dirname, file), mapping_key=_clean(file))

            @pipeline
            def process_directory():
                files = files_in_directory()

                # use map to invoke a solid on each dynamic output
                file_results = files.map(process_file)

                # use collect to gather the results in to a list
                summarize_directory(file_results.collect())
    """

    @property
    def is_dynamic(self):
        return True


class OutputPointer(namedtuple("_OutputPointer", "solid_name output_name")):
    def __new__(cls, solid_name, output_name=None):
        return super(OutputPointer, cls).__new__(
            cls,
            check.str_param(solid_name, "solid_name"),
            check.opt_str_param(output_name, "output_name", DEFAULT_OUTPUT),
        )


class OutputMapping(namedtuple("_OutputMapping", "definition maps_from")):
    """Defines an output mapping for a composite solid.

    Args:
        definition (OutputDefinition): Defines the output of the composite solid.
        solid_name (str): The name of the child solid from which to map the output.
        output_name (str): The name of the child solid's output from which to map the output.
    """

    def __new__(cls, definition, maps_from):
        return super(OutputMapping, cls).__new__(
            cls,
            check.inst_param(definition, "definition", OutputDefinition),
            check.inst_param(maps_from, "maps_from", OutputPointer),
        )


class Out(
    NamedTuple(
        "_Out",
        [
            ("dagster_type", Union[DagsterType, Type[NoValueSentinel]]),
            ("description", Optional[str]),
            ("is_required", Optional[bool]),
            ("io_manager_key", Optional[str]),
            ("metadata", Optional[Dict[str, Any]]),
        ],
    )
):
    """
    Defines an output from an op's compute function.

    Ops can have multiple outputs, in which case outputs cannot be anonymous.

    Many ops have only one output, in which case the user can provide a single output definition
    that will be given the default name, "result".

    Outs may be typed using the Dagster type system.

    Args:
        dagster_type (Optional[Union[Type, DagsterType]]]):
            The type of this output. Should only be set if the correct type can not
            be inferred directly from the type signature of the decorated function.
        description (Optional[str]): Human-readable description of the output.
        is_required (Optional[bool]): Whether the presence of this field is required. (default: True)
        io_manager_key (Optional[str]): The resource key of the output manager used for this output.
            (default: "io_manager").
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the output.
            For example, users can provide a file path if the data object will be stored in a
            filesystem, or provide information of a database table when it is going to load the data
            into the table.
    """

    def __new__(
        cls,
        dagster_type=NoValueSentinel,
        description=None,
        is_required=None,
        io_manager_key=None,
        metadata=None,
    ):
        return super(Out, cls).__new__(
            cls,
            dagster_type=dagster_type,
            description=description,
            is_required=is_required,
            io_manager_key=io_manager_key,
            metadata=metadata,
        )

    def to_definition(self, annotation_type: type, name: Optional[str]) -> "OutputDefinition":
        dagster_type = (
            self.dagster_type if self.dagster_type is not NoValueSentinel else annotation_type
        )

        return OutputDefinition(
            dagster_type=dagster_type,
            name=name,
            description=self.description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
        )


class AssetOut(Out):
    """
    Variant of :py:class:`Out <dagster.Out>` for an output that will be used to generate a tracked
    asset at runtime.

    Args:
        asset_key (Union[AssetKey, str, Sequence[str]]): The AssetKey representing the asset that
            will be updated using the data associated with this output.
        dagster_type (Optional[Union[Type, DagsterType]]]):
            The type of this output. Should only be set if the correct type can not
            be inferred directly from the type signature of the decorated function.
        description (Optional[str]): Human-readable description of the output.
        is_required (Optional[bool]): Whether the presence of this field is required. (default: True)
        io_manager_key (Optional[str]): The resource key of the output manager used for this output.
            (default: "io_manager").
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the output.
            For example, users can provide a file path if the data object will be stored in a
            filesystem, or provide information of a database table when it is going to load the data
            into the table.
        asset_partitions_fn (Optional[OutputContext -> Set[str]]): A function that produces a set of
            partitions from the OutputContext) which should be associated with this Out.
        asset_partitions_def (Optional[PartitionsDefinition]): Defines the entire set of partitions
            on the asset associated with this AssetOut.
        dependencies (Optional[Union[Set[AssetKey], Sequence[AssetKey]]]): The set of AssetKeys
            that this particular AssetOut depends on. If not included, this set will be inferred
            to be the set of AssetKeys attached to inputs of this AssetOut's Op.
    """

    _asset_key: AssetKey
    _asset_partitions_fn: Any
    _asset_partitions_def: Any
    _dependencies: Optional[Set[AssetKey]]

    def __new__(
        cls,
        asset_key: Union[AssetKey, str, Sequence[str]],
        dagster_type=NoValueSentinel,
        description: str = None,
        is_required: bool = None,
        io_manager_key: str = None,
        metadata: Mapping[str, Any] = None,
        asset_partitions_fn=None,
        asset_partitions_def=None,
        dependencies: Optional[Union[Set[AssetKey], Sequence[AssetKey]]] = None,
    ):
        instance = super().__new__(
            cls,
            dagster_type=dagster_type,
            description=description,
            is_required=is_required,
            io_manager_key=io_manager_key,
            metadata=metadata,
        )

        instance._asset_key = asset_key if isinstance(asset_key, AssetKey) else AssetKey(asset_key)
        instance._asset_partitions_fn = asset_partitions_fn
        instance._asset_partitions_def = asset_partitions_def

        # coerce to list for convenience
        if isinstance(dependencies, list):
            dependencies = set(dependencies)
        check.opt_set_param(dependencies, "dependencies", AssetKey)
        instance._dependencies = dependencies
        return instance

    @property
    def asset_key(self) -> AssetKey:
        return self._asset_key

    @property
    def asset_partitions_def(self):
        return self._asset_partitions_def

    @property
    def dependencies(self) -> Optional[Set[AssetKey]]:
        return self._dependencies

    def to_definition(self, annotation_type: type, name: Optional[str]) -> "OutputDefinition":
        dagster_type = (
            self.dagster_type if self.dagster_type is not NoValueSentinel else annotation_type
        )

        return AssetOutputDefinition(
            dagster_type=dagster_type,
            name=name,
            description=self.description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
            asset_key=self.asset_key,
            asset_partitions_fn=self._asset_partitions_fn,
            asset_partitions_def=self.asset_partitions_def,
            dependencies=self.dependencies,
        )


class DynamicOut(Out):
    """
    Variant of :py:class:`Out <dagster.Out>` for an output that will dynamically alter the graph at
    runtime.

    When using in a composition function such as :py:func:`@graph <dagster.graph>`,
    dynamic outputs must be used with either

    * ``map`` - clone downstream ops for each separate :py:class:`DynamicOut`
    * ``collect`` - gather across all :py:class:`DynamicOut` in to a list

    Uses the same constructor as :py:class:`Out <dagster.Out>`

        .. code-block:: python

            @op(
                config_schema={
                    "path": Field(str, default_value=file_relative_path(__file__, "sample"))
                },
                out=DynamicOut(str),
            )
            def files_in_directory(context):
                path = context.op_config["path"]
                dirname, _, filenames = next(os.walk(path))
                for file in filenames:
                    yield DynamicOutput(os.path.join(dirname, file), mapping_key=_clean(file))

            @job
            def process_directory():
                files = files_in_directory()

                # use map to invoke an op on each dynamic output
                file_results = files.map(process_file)

                # use collect to gather the results in to a list
                summarize_directory(file_results.collect())
    """

    def to_definition(self, annotation_type: type, name: Optional[str]) -> "OutputDefinition":
        dagster_type = (
            self.dagster_type if self.dagster_type is not NoValueSentinel else annotation_type
        )

        return DynamicOutputDefinition(
            dagster_type=dagster_type,
            name=name,
            description=self.description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
        )


class GraphOut(NamedTuple("_GraphOut", [("description", Optional[str])])):
    """
    Represents information about the outputs that a graph maps.

    Args:
        description (Optional[str]): Human-readable description of the output.
    """

    def __new__(cls, description=None):
        return super(GraphOut, cls).__new__(cls, description=description)

    def to_definition(self, name: Optional[str]) -> "OutputDefinition":
        return OutputDefinition(name=name, description=self.description)

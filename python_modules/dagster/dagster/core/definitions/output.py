import warnings
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    List,
    NamedTuple,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
from dagster.core.definitions.events import AssetKey, DynamicAssetKey
from dagster.core.definitions.metadata import MetadataEntry, MetadataUserInput, normalize_metadata
from dagster.core.errors import DagsterError, DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import (
    DagsterType,
    is_dynamic_output_annotation,
    resolve_dagster_type,
)
from dagster.utils.backcompat import experimental_arg_warning

from .inference import InferredOutputProps
from .input import NoValueSentinel
from .utils import DEFAULT_OUTPUT, check_valid_name

if TYPE_CHECKING:
    from dagster.core.definitions.partition import PartitionsDefinition
    from dagster.core.execution.context.output import OutputContext

TOut = TypeVar("TOut", bound="OutputDefinition")


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
        asset_key (Optional[AssetKey]]): (Experimental) An AssetKey which should be associated
            with this OutputDefinition. Used for tracking lineage information through Dagster.
        asset_partitions (Optional[Union[Set[str], OutputContext -> Set[str]]]): (Experimental) A
            set of partitions of the given asset_key (or a function that produces this list of
            partitions from the OutputContext) which should be associated with this OutputDefinition.
    """

    def __init__(
        self,
        dagster_type=None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_required: bool = True,
        io_manager_key: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        asset_key: Optional[Union[AssetKey, DynamicAssetKey]] = None,
        asset_partitions: Optional[
            Union[AbstractSet[str], Callable[["OutputContext"], AbstractSet[str]]]
        ] = None,
        asset_partitions_def: Optional["PartitionsDefinition"] = None
        # make sure new parameters are updated in combine_with_inferred below
    ):
        from dagster.core.definitions.partition import PartitionsDefinition

        self._name = check_valid_name(check.opt_str_param(name, "name", DEFAULT_OUTPUT))
        self._type_not_set = dagster_type is None
        self._dagster_type = resolve_dagster_type(dagster_type)
        self._description = check.opt_str_param(description, "description")
        self._is_required = check.bool_param(is_required, "is_required")
        self._io_manager_key = check.opt_str_param(
            io_manager_key,
            "io_manager_key",
            default="io_manager",
        )
        self._metadata = check.opt_dict_param(metadata, "metadata", key_type=str)
        self._metadata_entries = check.is_list(
            normalize_metadata(self._metadata, [], allow_invalid=True), MetadataEntry
        )

        if asset_key:
            experimental_arg_warning("asset_key", "OutputDefinition.__init__")

        if callable(asset_key):
            warnings.warn(
                "Passing a function as the `asset_key` argument to `Out` or `OutputDefinition` is "
                "deprecated behavior and will be removed in version 0.15.0."
            )
        else:
            check.opt_inst_param(asset_key, "asset_key", AssetKey)

        self._asset_key = asset_key

        if asset_partitions:
            experimental_arg_warning("asset_partitions", "OutputDefinition.__init__")
            check.param_invariant(
                asset_key is not None,
                "asset_partitions",
                'Cannot specify "asset_partitions" argument without also specifying "asset_key"',
            )

        self._asset_partitions_fn: Optional[Callable[["OutputContext"], AbstractSet[str]]]
        if callable(asset_partitions):
            self._asset_partitions_fn = asset_partitions
        elif asset_partitions is not None:
            asset_partitions = check.opt_set_param(asset_partitions, "asset_partitions", str)

            def _fn(_context: "OutputContext") -> AbstractSet[str]:
                return cast(AbstractSet[str], asset_partitions)  # mypy bug?

            self._asset_partitions_fn = _fn
        else:
            self._asset_partitions_fn = None

        if asset_partitions_def:
            experimental_arg_warning("asset_partitions_def", "OutputDefinition.__init__")
        self._asset_partitions_def = check.opt_inst_param(
            asset_partitions_def, "asset_partition_def", PartitionsDefinition
        )

    @property
    def name(self):
        return self._name

    @property
    def dagster_type(self) -> DagsterType:
        return self._dagster_type

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def is_required(self) -> bool:
        return self._is_required

    @property
    def io_manager_key(self) -> str:
        return self._io_manager_key

    @property
    def optional(self) -> bool:
        return not self.is_required

    @property
    def metadata(self) -> MetadataUserInput:
        return self._metadata

    @property
    def metadata_entries(self) -> List[MetadataEntry]:
        return self._metadata_entries

    @property
    def is_dynamic(self) -> bool:
        return False

    @property
    def is_asset(self) -> bool:
        return self._asset_key is not None

    @property
    def asset_partitions_def(self) -> Optional["PartitionsDefinition"]:
        return self._asset_partitions_def

    @property
    def hardcoded_asset_key(self) -> Optional[AssetKey]:
        if not callable(self._asset_key):
            return self._asset_key
        else:
            return None

    def get_asset_key(self, context: "OutputContext") -> Optional[AssetKey]:
        """Get the AssetKey associated with this OutputDefinition for the given
        :py:class:`OutputContext` (if any).

        Args:
            context (OutputContext): The OutputContext that this OutputDefinition is being evaluated
                in
        """
        if callable(self._asset_key):
            return self._asset_key(context)
        else:
            return self.hardcoded_asset_key

    def get_asset_partitions(self, context: "OutputContext") -> Optional[AbstractSet[str]]:
        """Get the set of partitions associated with this OutputDefinition for the given
        :py:class:`OutputContext` (if any).

        Args:
            context (OutputContext): The OutputContext that this OutputDefinition is being evaluated
            in
        """
        if self._asset_partitions_fn is None:
            return None

        return self._asset_partitions_fn(context)

    def mapping_from(self, solid_name: str, output_name: Optional[str] = None) -> "OutputMapping":
        """Create an output mapping from an output of a child solid.

        In a CompositeSolidDefinition, you can use this helper function to construct
        an :py:class:`OutputMapping` from the output of a child solid.

        Args:
            solid_name (str): The name of the child solid from which to map this output.
            output_name (str): The name of the child solid's output from which to map this output.

        Examples:

            .. code-block:: python

                output_mapping = OutputDefinition(Int).mapping_from('child_solid')
        """
        return OutputMapping(self, OutputPointer(solid_name, output_name))

    @staticmethod
    def create_from_inferred(inferred: InferredOutputProps) -> "OutputDefinition":
        if is_dynamic_output_annotation(inferred.annotation):
            return DynamicOutputDefinition(
                dagster_type=_checked_inferred_type(inferred.annotation),
                description=inferred.description,
            )
        else:
            return OutputDefinition(
                dagster_type=_checked_inferred_type(inferred.annotation),
                description=inferred.description,
            )

    def combine_with_inferred(self: TOut, inferred: InferredOutputProps) -> TOut:
        dagster_type = self.dagster_type
        if self._type_not_set:
            dagster_type = _checked_inferred_type(inferred.annotation)
        if self.description is None:
            description = inferred.description
        else:
            description = self.description

        return self.__class__(
            name=self.name,
            dagster_type=dagster_type,
            description=description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self._metadata,
            asset_key=self._asset_key,
            asset_partitions=self._asset_partitions_fn,
            asset_partitions_def=self.asset_partitions_def,
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
    def is_dynamic(self) -> bool:
        return True


class OutputPointer(NamedTuple("_OutputPointer", [("solid_name", str), ("output_name", str)])):
    def __new__(cls, solid_name: str, output_name: Optional[str] = None):
        return super(OutputPointer, cls).__new__(
            cls,
            check.str_param(solid_name, "solid_name"),
            check.opt_str_param(output_name, "output_name", DEFAULT_OUTPUT),
        )

    @property
    def node_name(self):
        return self.solid_name


class OutputMapping(
    NamedTuple("_OutputMapping", [("definition", OutputDefinition), ("maps_from", OutputPointer)])
):
    """Defines an output mapping for a composite solid.

    Args:
        definition (OutputDefinition): Defines the output of the composite solid.
        solid_name (str): The name of the child solid from which to map the output.
        output_name (str): The name of the child solid's output from which to map the output.
    """

    def __new__(cls, definition: OutputDefinition, maps_from: OutputPointer):
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
            ("is_required", bool),
            ("io_manager_key", str),
            ("metadata", Optional[MetadataUserInput]),
            ("asset_key", Optional[Union[AssetKey, DynamicAssetKey]]),
            (
                "asset_partitions",
                Optional[Union[AbstractSet[str], Callable[["OutputContext"], AbstractSet[str]]]],
            ),
            ("asset_partitions_def", Optional["PartitionsDefinition"]),
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
        is_required (bool): Whether the presence of this field is required. (default: True)
        io_manager_key (Optional[str]): The resource key of the output manager used for this output.
            (default: "io_manager").
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the output.
            For example, users can provide a file path if the data object will be stored in a
            filesystem, or provide information of a database table when it is going to load the data
            into the table.
        asset_key (Optional[AssetKey]): (Experimental) An AssetKey which should be associated
            with this Out. Used for tracking lineage information through Dagster.
        asset_partitions (Optional[Union[Set[str], OutputContext -> Set[str]]]): (Experimental) A
            set of partitions of the given asset_key (or a function that produces this list of
            partitions from the OutputContext) which should be associated with this Out.
    """

    def __new__(
        cls,
        dagster_type: Union[Type, DagsterType] = NoValueSentinel,
        description: Optional[str] = None,
        is_required: bool = True,
        io_manager_key: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        asset_key: Optional[AssetKey] = None,
        asset_partitions: Optional[
            Union[AbstractSet[str], Callable[["OutputContext"], AbstractSet[str]]]
        ] = None,
        asset_partitions_def: Optional["PartitionsDefinition"] = None,
        # make sure new parameters are updated in combine_with_inferred below
    ):
        if asset_partitions_def:
            experimental_arg_warning("asset_partitions_definition", "Out.__new__")
        return super(Out, cls).__new__(
            cls,
            dagster_type=NoValueSentinel
            if dagster_type is NoValueSentinel
            else resolve_dagster_type(dagster_type),
            description=description,
            is_required=check.bool_param(is_required, "is_required"),
            io_manager_key=check.opt_str_param(
                io_manager_key, "io_manager_key", default="io_manager"
            ),
            metadata=metadata,
            asset_key=asset_key,
            asset_partitions=asset_partitions,
            asset_partitions_def=asset_partitions_def,
        )

    @staticmethod
    def from_definition(output_def: "OutputDefinition"):
        return Out(
            dagster_type=output_def.dagster_type,
            description=output_def.description,
            is_required=output_def.is_required,
            io_manager_key=output_def.io_manager_key,
            metadata=output_def.metadata,
            asset_key=output_def._asset_key,  # type: ignore # pylint: disable=protected-access
            asset_partitions=output_def._asset_partitions_fn,  # pylint: disable=protected-access
            asset_partitions_def=output_def.asset_partitions_def,  # pylint: disable=protected-access
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
            asset_key=self.asset_key,
            asset_partitions=self.asset_partitions,
            asset_partitions_def=self.asset_partitions_def,
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
            asset_key=self.asset_key,
            asset_partitions=self.asset_partitions,
        )


class GraphOut(NamedTuple("_GraphOut", [("description", Optional[str])])):
    """
    Represents information about the outputs that a graph maps.

    Args:
        description (Optional[str]): Human-readable description of the output.
    """

    def __new__(cls, description: Optional[str] = None):
        return super(GraphOut, cls).__new__(cls, description=description)

    def to_definition(self, name: Optional[str]) -> "OutputDefinition":
        return OutputDefinition(name=name, description=self.description)

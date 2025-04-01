import inspect
from typing import Any, NamedTuple, Optional, TypeVar, Union

import dagster._check as check
from dagster._annotations import PublicAttr, deprecated_param
from dagster._core.definitions.inference import InferredOutputProps
from dagster._core.definitions.input import NoValueSentinel
from dagster._core.definitions.metadata import (
    ArbitraryMetadataMapping,
    RawMetadataMapping,
    normalize_metadata,
)
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY, DEFAULT_OUTPUT, check_valid_name
from dagster._core.errors import DagsterError, DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import (
    DagsterType,
    is_dynamic_output_annotation,
    resolve_dagster_type,
)

TOutputDefinition = TypeVar("TOutputDefinition", bound="OutputDefinition")
TOut = TypeVar("TOut", bound="Out")


class OutputDefinition:
    """Defines an output from an op's compute function.

    Ops can have multiple outputs, in which case outputs cannot be anonymous.

    Many ops have only one output, in which case the user can provide a single output definition
    that will be given the default name, "result".

    Output definitions may be typed using the Dagster type system.

    Args:
        dagster_type (Optional[Union[Type, DagsterType]]]): The type of this output.
            Users should provide the Python type of the objects that they expect the op to yield
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
        code_version (Optional[str]): Version of the code that generates this output. In
            general, versions should be set only for code that deterministically produces the same
            output when given the same inputs.

    """

    def __init__(
        self,
        dagster_type=None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_required: bool = True,
        io_manager_key: Optional[str] = None,
        metadata: Optional[ArbitraryMetadataMapping] = None,
        code_version: Optional[str] = None,
        # make sure new parameters are updated in combine_with_inferred below
    ):
        self._name = check_valid_name(check.opt_str_param(name, "name", DEFAULT_OUTPUT))
        self._type_not_set = dagster_type is None
        self._dagster_type = resolve_dagster_type(dagster_type)
        self._description = check.opt_str_param(description, "description")
        self._is_required = check.bool_param(is_required, "is_required")
        self._io_manager_key = check.opt_str_param(
            io_manager_key,
            "io_manager_key",
            default=DEFAULT_IO_MANAGER_KEY,
        )
        self._code_version = check.opt_str_param(code_version, "code_version")
        self._raw_metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self._metadata = normalize_metadata(self._raw_metadata, allow_invalid=True)

    @property
    def name(self) -> str:
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
    def code_version(self) -> Optional[str]:
        return self._code_version

    @property
    def optional(self) -> bool:
        return not self.is_required

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self._raw_metadata

    @property
    def is_dynamic(self) -> bool:
        return False

    def mapping_from(
        self, node_name: str, output_name: Optional[str] = None, from_dynamic_mapping: bool = False
    ) -> "OutputMapping":
        """Create an output mapping from an output of a child node.

        In a GraphDefinition, you can use this helper function to construct
        an :py:class:`OutputMapping` from the output of a child node.

        Args:
            node_name (str): The name of the child node from which to map this output.
            output_name (str): The name of the child node's output from which to map this output.

        Examples:
            .. code-block:: python

                output_mapping = OutputDefinition(Int).mapping_from('child_node')
        """
        return OutputMapping(
            graph_output_name=self.name,
            mapped_node_name=node_name,
            mapped_node_output_name=output_name or DEFAULT_OUTPUT,
            graph_output_description=self.description,
            dagster_type=self.dagster_type,
            from_dynamic_mapping=from_dynamic_mapping or self.is_dynamic,
        )

    @staticmethod
    def create_from_inferred(
        inferred: Optional[InferredOutputProps], code_version: Optional[str] = None
    ) -> "OutputDefinition":
        if not inferred:
            return OutputDefinition(code_version=code_version)
        if is_dynamic_output_annotation(inferred.annotation):
            return DynamicOutputDefinition(
                dagster_type=_checked_inferred_type(inferred.annotation),
                description=inferred.description,
                code_version=code_version,
            )
        else:
            return OutputDefinition(
                dagster_type=_checked_inferred_type(inferred.annotation),
                description=inferred.description,
                code_version=code_version,
            )

    def combine_with_inferred(
        self: TOutputDefinition, inferred: InferredOutputProps
    ) -> TOutputDefinition:
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
        )


def _checked_inferred_type(inferred: Any) -> DagsterType:
    try:
        if inferred == inspect.Parameter.empty:
            return resolve_dagster_type(None)
        elif inferred is None:
            # When inferred.annotation is None, it means someone explicitly put "None" as the
            # annotation, so want to map it to a DagsterType that checks for the None type
            return resolve_dagster_type(type(None))
        else:
            return resolve_dagster_type(inferred)

    except DagsterError as e:
        raise DagsterInvalidDefinitionError(
            f"Problem using type '{inferred}' from return type annotation, correct the issue "
            "or explicitly set the dagster_type via Out()."
        ) from e


class DynamicOutputDefinition(OutputDefinition):
    """Variant of :py:class:`OutputDefinition <dagster.OutputDefinition>` for an
    output that will dynamically alter the graph at runtime.

    When using in a composition function such as :py:func:`@job <dagster.job>`,
    dynamic outputs must be used with either:

    * ``map`` - clone downstream nodes for each separate :py:class:`DynamicOutput`
    * ``collect`` - gather across all :py:class:`DynamicOutput` in to a list

    Uses the same constructor as :py:class:`OutputDefinition <dagster.OutputDefinition>`

        .. code-block:: python

            @op(
                config_schema={
                    "path": Field(str, default_value=file_relative_path(__file__, "sample"))
                },
                output_defs=[DynamicOutputDefinition(str)],
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

    @property
    def is_dynamic(self) -> bool:
        return True


class OutputPointer(NamedTuple("_OutputPointer", [("node_name", str), ("output_name", str)])):
    def __new__(cls, node_name: str, output_name: Optional[str] = None):
        return super().__new__(
            cls,
            check.str_param(node_name, "node_name"),
            check.opt_str_param(output_name, "output_name", DEFAULT_OUTPUT),
        )


@deprecated_param(
    param="dagster_type",
    breaking_version="2.0",
    additional_warn_text="Any defined `dagster_type` should come from the underlying op `Output`.",
    # Disabling warning here since we're passing this internally and I'm not sure whether it is
    # actually used or discarded.
    emit_runtime_warning=False,
)
class OutputMapping(NamedTuple):
    """Defines an output mapping for a graph.

    Args:
        graph_output_name (str): Name of the output in the graph being mapped to.
        mapped_node_name (str): Named of the node (op/graph) that the output is being mapped from.
        mapped_node_output_name (str): Name of the output in the node (op/graph) that is being mapped from.
        graph_output_description (Optional[str]): A description of the output in the graph being mapped from.
        from_dynamic_mapping (bool): Set to true if the node being mapped to is a mapped dynamic node.
        dagster_type (Optional[DagsterType]): The dagster type of the graph's output being mapped to.

    Examples:
        .. code-block:: python

            from dagster import OutputMapping, GraphDefinition, op, graph, GraphOut

            @op
            def emit_five(x):
                return 5

            # The following two graph definitions are equivalent
            GraphDefinition(
                name="the_graph",
                node_defs=[emit_five],
                output_mappings=[
                    OutputMapping(
                        graph_output_name="result", # Default output name
                        mapped_node_name="emit_five",
                        mapped_node_output_name="result"
                    )
                ]
            )

            @graph(out=GraphOut())
            def the_graph:
                return emit_five()
    """

    graph_output_name: str
    mapped_node_name: str
    mapped_node_output_name: str
    graph_output_description: Optional[str] = None
    dagster_type: Optional[DagsterType] = None
    from_dynamic_mapping: bool = False

    @property
    def maps_from(self) -> OutputPointer:
        return OutputPointer(self.mapped_node_name, self.mapped_node_output_name)

    def get_definition(self, is_dynamic: bool) -> "OutputDefinition":
        check.invariant(not is_dynamic or self.from_dynamic_mapping)
        is_dynamic = is_dynamic or self.from_dynamic_mapping
        klass = DynamicOutputDefinition if is_dynamic else OutputDefinition
        return klass(
            name=self.graph_output_name,
            description=self.graph_output_description,
            dagster_type=self.dagster_type,
        )


class Out(
    NamedTuple(
        "_Out",
        [
            ("dagster_type", PublicAttr[Union[DagsterType, type[NoValueSentinel]]]),
            ("description", PublicAttr[Optional[str]]),
            ("is_required", PublicAttr[bool]),
            ("io_manager_key", PublicAttr[str]),
            ("metadata", PublicAttr[Optional[RawMetadataMapping]]),
            ("code_version", PublicAttr[Optional[str]]),
        ],
    )
):
    """Defines an output from an op's compute function.

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
        code_version (Optional[str]): Version of the code that generates this output. In
            general, versions should be set only for code that deterministically produces the same
            output when given the same inputs.
    """

    def __new__(
        cls,
        dagster_type: Optional[Union[type, DagsterType]] = NoValueSentinel,
        description: Optional[str] = None,
        is_required: bool = True,
        io_manager_key: Optional[str] = None,
        metadata: Optional[ArbitraryMetadataMapping] = None,
        code_version: Optional[str] = None,
        # make sure new parameters are updated in combine_with_inferred below
    ):
        return super().__new__(
            cls,
            dagster_type=(
                NoValueSentinel
                if dagster_type is NoValueSentinel
                else resolve_dagster_type(dagster_type)
            ),
            description=description,
            is_required=check.bool_param(is_required, "is_required"),
            io_manager_key=check.opt_str_param(
                io_manager_key, "io_manager_key", default=DEFAULT_IO_MANAGER_KEY
            ),
            metadata=metadata,
            code_version=code_version,
        )

    @classmethod
    def from_definition(cls, output_def: "OutputDefinition"):
        klass = Out if not output_def.is_dynamic else DynamicOut
        return klass(
            dagster_type=output_def.dagster_type,
            description=output_def.description,
            is_required=output_def.is_required,
            io_manager_key=output_def.io_manager_key,
            metadata=output_def.metadata,
            code_version=output_def.code_version,
        )

    def to_definition(
        self,
        annotation_type: type,
        name: Optional[str],
        description: Optional[str],
        code_version: Optional[str],
    ) -> "OutputDefinition":
        dagster_type = (
            self.dagster_type
            if self.dagster_type is not NoValueSentinel
            else _checked_inferred_type(annotation_type)
        )

        klass = OutputDefinition if not self.is_dynamic else DynamicOutputDefinition

        return klass(
            dagster_type=dagster_type,
            name=name,
            description=self.description or description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
            code_version=self.code_version or code_version,
        )

    @property
    def is_dynamic(self) -> bool:
        return False


class DynamicOut(Out):
    """Variant of :py:class:`Out <dagster.Out>` for an output that will dynamically alter the graph at
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

    def to_definition(
        self,
        annotation_type: type,
        name: Optional[str],
        description: Optional[str],
        code_version: Optional[str],
    ) -> "OutputDefinition":
        dagster_type = (
            self.dagster_type
            if self.dagster_type is not NoValueSentinel
            else _checked_inferred_type(annotation_type)
        )

        return DynamicOutputDefinition(
            dagster_type=dagster_type,
            name=name,
            description=self.description or description,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            metadata=self.metadata,
            code_version=self.code_version or code_version,
        )

    @property
    def is_dynamic(self) -> bool:
        return True


class GraphOut(NamedTuple("_GraphOut", [("description", PublicAttr[Optional[str]])])):
    """Represents information about the outputs that a graph maps.

    Args:
        description (Optional[str]): Human-readable description of the output.
    """

    def __new__(cls, description: Optional[str] = None):
        return super().__new__(cls, description=description)

    def to_definition(self, name: Optional[str]) -> "OutputDefinition":
        return OutputDefinition(name=name, description=self.description)

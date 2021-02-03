import warnings
from abc import abstractmethod, abstractproperty

from dagster import check
from dagster.core.definitions.configurable import NamedConfigurableDefinition
from dagster.utils import frozendict, frozenlist

from .hook import HookDefinition
from .utils import check_valid_name, validate_tags


# base class for SolidDefinition and GraphDefinition
# represents that this is embedable within a graph
class NodeDefinition(NamedConfigurableDefinition):
    def __init__(
        self,
        name,
        input_defs,
        output_defs,
        description=None,
        tags=None,
        positional_inputs=None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._tags = validate_tags(tags)
        self._input_defs = frozenlist(input_defs)
        self._input_dict = frozendict({input_def.name: input_def for input_def in input_defs})
        check.invariant(len(self._input_defs) == len(self._input_dict), "Duplicate input def names")
        self._output_defs = frozenlist(output_defs)
        self._output_dict = frozendict({output_def.name: output_def for output_def in output_defs})
        check.invariant(
            len(self._output_defs) == len(self._output_dict), "Duplicate output def names"
        )
        check.opt_list_param(positional_inputs, "positional_inputs", str)
        self._positional_inputs = (
            positional_inputs
            if positional_inputs is not None
            else list(map(lambda inp: inp.name, input_defs))
        )

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def tags(self):
        return self._tags

    @property
    def positional_inputs(self):
        return self._positional_inputs

    @property
    def input_defs(self):
        return self._input_defs

    @property
    def input_dict(self):
        return self._input_dict

    def resolve_input_name_at_position(self, idx):
        if idx >= len(self._positional_inputs):
            if not (
                len(self._input_defs) - len(self._positional_inputs) == 1
                and idx == len(self._input_defs) - 1
            ):
                return None

            # handle special case where there is only 1 non-positional arg that we could resolve to
            names = [
                inp.name for inp in self._input_defs if inp.name not in self._positional_inputs
            ]
            check.invariant(len(names) == 1, "if check above should prevent this")
            return names[0]

        return self._positional_inputs[idx]

    @property
    def output_defs(self):
        return self._output_defs

    @property
    def output_dict(self):
        return self._output_dict

    def has_input(self, name):
        check.str_param(name, "name")
        return name in self._input_dict

    def input_def_named(self, name):
        check.str_param(name, "name")
        return self._input_dict[name]

    def has_output(self, name):
        check.str_param(name, "name")
        return name in self._output_dict

    def output_def_named(self, name):
        check.str_param(name, "name")
        return self._output_dict[name]

    @property
    def has_configurable_inputs(self):
        warnings.warn(
            "NodeDefinition.has_configurable_inputs is deprecated, starting in 0.10.0, because "
            "whether the node has configurable inputs depends on what RootInputManager is supplied "
            "in the mode."
        )
        return any([inp.dagster_type.loader or inp.root_manager_key for inp in self._input_defs])

    @property
    def has_configurable_outputs(self):
        warnings.warn(
            "NodeDefinition.has_configurable_inputs is deprecated, starting in 0.10.0, because "
            "whether the node has configurable inputs depends on what IOManager is supplied in the "
            " mode."
        )
        return any([out.dagster_type.materializer for out in self._output_defs])

    @abstractproperty
    def has_config_entry(self):
        raise NotImplementedError()

    @abstractmethod
    def iterate_node_defs(self):
        raise NotImplementedError()

    @abstractmethod
    def resolve_output_to_origin(self, output_name, handle):
        raise NotImplementedError()

    @abstractmethod
    def input_has_default(self, input_name):
        raise NotImplementedError()

    @abstractmethod
    def default_value_for_input(self, input_name):
        raise NotImplementedError()

    @abstractmethod
    def input_supports_dynamic_output_dep(self, input_name):
        raise NotImplementedError()

    def all_input_output_types(self):
        for input_def in self._input_defs:
            yield input_def.dagster_type
            yield from input_def.dagster_type.inner_types

        for output_def in self._output_defs:
            yield output_def.dagster_type
            yield from output_def.dagster_type.inner_types

    def __call__(self, *args, **kwargs):
        from .composition import CallableNode

        return CallableNode(self)(*args, **kwargs)

    def alias(self, name):
        from .composition import CallableNode

        check.str_param(name, "name")

        return CallableNode(self, given_alias=name)

    def tag(self, tags):
        from .composition import CallableNode

        return CallableNode(self, tags=validate_tags(tags))

    def with_hooks(self, hook_defs):
        from .composition import CallableNode

        hook_defs = frozenset(check.set_param(hook_defs, "hook_defs", of_type=HookDefinition))

        return CallableNode(self, hook_defs=hook_defs)

    @abstractproperty
    def required_resource_keys(self):
        raise NotImplementedError()

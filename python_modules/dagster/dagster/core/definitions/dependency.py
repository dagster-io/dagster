from collections import defaultdict, namedtuple

from dagster import check

from .solid import SolidDefinition

from .input import InputDefinition

from .output import OutputDefinition

from .utils import DEFAULT_OUTPUT, check_two_dim_str_dict, struct_to_string


class SolidInstance(namedtuple('Solid', 'name alias')):
    '''
    A solid identifier in a dependency structure. Allows supplying parameters to the solid,
    like the alias.

    Example:

        .. code-block:: python

            pipeline = Pipeline(
                solids=[solid_1, solid_2]
                dependencies={
                    SolidInstance('solid_2', alias='other_name') : {
                        'input_name' : DependencyDefinition('solid_2'),
                    },
                    'solid_1' : {
                        'input_name': DependencyDefinition('other_name'),
                    },
                }
            )
    '''

    def __new__(cls, name, alias=None):
        name = check.str_param(name, 'name')
        alias = check.opt_str_param(alias, 'alias')
        return super(cls, SolidInstance).__new__(cls, name, alias)


class Solid(object):
    '''
    Solid instance within a pipeline. Defined by it's name inside the pipeline.

    Attributes:
        name (str):
            Name of the solid inside the pipeline. Must be unique per-pipeline.
        definition (SolidDefinition):
            Definition of the solid.
    '''

    def __init__(self, name, definition):
        self.name = check.str_param(name, 'name')
        self.definition = check.inst_param(definition, 'definition', SolidDefinition)

        input_handles = {}
        for input_def in self.definition.input_defs:
            input_handles[input_def.name] = SolidInputHandle(self, input_def)

        self._input_handles = input_handles

        output_handles = {}
        for output_def in self.definition.output_defs:
            output_handles[output_def.name] = SolidOutputHandle(self, output_def)

        self._output_handles = output_handles

    def input_handles(self):
        return self._input_handles.values()

    def output_handles(self):
        return self._output_handles.values()

    def input_handle(self, name):
        check.str_param(name, 'name')
        return self._input_handles[name]

    def output_handle(self, name):
        check.str_param(name, 'name')
        return self._output_handles[name]

    def has_input(self, name):
        return self.definition.has_input(name)

    def input_def_named(self, name):
        return self.definition.input_def_named(name)

    def has_output(self, name):
        return self.definition.has_output(name)

    def output_def_named(self, name):
        return self.definition.output_def_named(name)

    @property
    def input_defs(self):
        return self.definition.input_defs

    @property
    def output_defs(self):
        return self.definition.output_defs


class SolidInputHandle(namedtuple('_SolidInputHandle', 'solid input_def')):
    def __new__(cls, solid, input_def):
        return super(SolidInputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(input_def, 'input_def', InputDefinition),
        )

    def _inner_str(self):
        return struct_to_string(
            'SolidInputHandle',
            solid_name=self.solid.name,
            definition_name=self.solid.definition.name,
            input_name=self.input_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.solid.name, self.input_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.input_def.name == other.input_def.name


class SolidOutputHandle(namedtuple('_SolidOutputHandle', 'solid output_def')):
    def __new__(cls, solid, output_def):
        return super(SolidOutputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(output_def, 'output_def', OutputDefinition),
        )

    def _inner_str(self):
        return struct_to_string(
            'SolidOutputHandle',
            solid_name=self.solid.name,
            definition_name=self.solid.definition.name,
            output_name=self.output_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.solid.name, self.output_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.output_def.name == other.output_def.name


class InputToOutputHandleDict(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidInputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidInputHandle)
        check.inst_param(val, 'val', SolidOutputHandle)
        return dict.__setitem__(self, key, val)


def _create_handle_dict(solid_dict, dep_dict):
    check.dict_param(solid_dict, 'solid_dict', key_type=str, value_type=Solid)
    check_two_dim_str_dict(dep_dict, 'dep_dict', DependencyDefinition)

    handle_dict = InputToOutputHandleDict()

    for solid_name, input_dict in dep_dict.items():
        for input_name, dep_def in input_dict.items():
            from_solid = solid_dict[solid_name]
            to_solid = solid_dict[dep_def.solid]
            handle_dict[from_solid.input_handle(input_name)] = to_solid.output_handle(
                dep_def.output
            )

    return handle_dict


class DependencyStructure(object):
    @staticmethod
    def from_definitions(solids, dep_dict):
        return DependencyStructure(_create_handle_dict(solids, dep_dict))

    def __init__(self, handle_dict):
        self._handle_dict = check.inst_param(handle_dict, 'handle_dict', InputToOutputHandleDict)

    def has_dep(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return solid_input_handle in self._handle_dict

    def deps_of_solid(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        return list(handles[1] for handles in self.__gen_deps_of_solid(solid_name))

    def deps_of_solid_with_input(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        return dict(self.__gen_deps_of_solid(solid_name))

    def __gen_deps_of_solid(self, solid_name):
        for input_handle, output_handle in self._handle_dict.items():
            if input_handle.solid.name == solid_name:
                yield (input_handle, output_handle)

    def depended_by_of_solid(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        result = defaultdict(list)
        for input_handle, output_handle in self._handle_dict.items():
            if output_handle.solid.name == solid_name:
                result[output_handle].append(input_handle)
        return result

    def get_dep(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return self._handle_dict[solid_input_handle]

    def input_handles(self):
        return list(self._handle_dict.keys())

    def items(self):
        return self._handle_dict.items()


class DependencyDefinition(namedtuple('_DependencyDefinition', 'solid output description')):
    '''Dependency definitions represent an edge in the DAG of solids. This object is
    used with a dictionary structure (whose keys represent solid/input where the dependency
    comes from) so this object only contains the target dependency information.

    Attributes:
        solid (str):
            The name of the solid that is the target of the dependency.
            This is the solid where the value passed between the solids
            comes from.
        output (str):
            The name of the output that is the target of the dependency.
            Defaults to "result", the default output name of solids with a single output.
        description (str):
            Description of this dependency. Optional.
    '''

    def __new__(cls, solid, output=DEFAULT_OUTPUT, description=None):
        return super(DependencyDefinition, cls).__new__(
            cls,
            check.str_param(solid, 'solid'),
            check.str_param(output, 'output'),
            check.opt_str_param(description, 'description'),
        )

from .builtin_enum import BuiltinEnum
from .config_schema import (
    input_hydration_config,
    input_selector_schema,
    output_materialization_config,
    output_selector_schema,
)
from .field import Field
from .field_utils import Dict, NamedDict, Selector, NamedSelector, PermissiveDict
from .runtime import PythonObjectType
from .wrapping import Optional, List

Any = BuiltinEnum.ANY
String = BuiltinEnum.STRING
Int = BuiltinEnum.INT
Bool = BuiltinEnum.BOOL
Path = BuiltinEnum.PATH
Float = BuiltinEnum.FLOAT
Nothing = BuiltinEnum.NOTHING


# What sort of witchcraft is this?

# Dagster actually has two type systems, one for *runtime* values, and one
# for schematizing config. However, we wish to avoid exposing the differences
# to users, so here we are. From their standpoint there is just one thing to
# deal with. That is why, for example, there are actually *three* different types
# of Lists in this submodule. One is the config version of "List; another is the
# runtime version of "List"; and the last is the user-facing version of List, that
# -- depending on context -- is converted (resolved, in the parlance) to either
# a config or a runtime type depending on whether it was, say passed into a Field
# (in which case it would be config version) or a InputDefinition (in which case it would be
# a runtime version.)

# This can be confusing, so we follow some naming conventions:

# 1. runtime_cls: Runtime types are singleton instances of a *class*. Users define
# classes and pass those in directly. When you know you are dealing with one of these
# classes, this should be the naming convention
# 2. config_cls: Similar to runtime_cls, but for config types.
# 3. runtime_type: When isinstance(runtime_type, RuntimeType) is guaranteed to be true.
# The general idiom is convert a {config,runtime}_cls to a type instance as soon as possible.
# The internal guts of all these systems operate on type instances for the most part.
# 4. config_type. When isinstance(config_type, ConfigType) is guaranteed to be true.
# 5. dagster_type. dagster_type is used for **user-facing** apis. These can be, very concretely,
# either builtin-primitives such as Dict, Field, Int, String and so forth, or user-defined types.

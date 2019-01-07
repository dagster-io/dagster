from .configurable import ConfigurableFromDict
from .materializable import Materializeable
from .builtins import is_wrapping_type


def iterate_types(dagster_type, seen_config_schemas):
    # HACK HACK HACK
    # This is quite terrible and stems from the confusion between
    # the runtime and config type systems. The problem here is that
    # materialization config schemas can themselves contain scalars
    # and without some kind of check we get into an infinite recursion
    # situation. The real fix will be to separate config and runtime types
    # in which case the config "Int" and the runtime "Int" will actually be
    # separate concepts

    if is_wrapping_type(dagster_type):
        for dt in iterate_types(dagster_type.inner_type, seen_config_schemas):
            yield dt
        return

    if isinstance(dagster_type, Materializeable):
        # Guaranteed to work after isinstance check
        # pylint: disable=E1101
        config_schema = dagster_type.define_materialization_config_schema()
        if not config_schema in seen_config_schemas:
            seen_config_schemas.add(config_schema)
            yield config_schema
            for inner_type in iterate_types(config_schema, seen_config_schemas):
                yield inner_type

    if isinstance(dagster_type, ConfigurableFromDict):
        for field_type in dagster_type.field_dict.values():
            for inner_type in iterate_types(field_type.dagster_type, seen_config_schemas):
                yield inner_type

    if dagster_type.is_named:
        yield dagster_type

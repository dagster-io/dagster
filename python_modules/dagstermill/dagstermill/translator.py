import papermill

RESERVED_INPUT_NAMES = [
    '__dm_context',
    '__dm_dagster',
    '__dm_dagster_cli_load_handle',
    '__dm_dagster_core_definitions_dependency',
    '__dm_dagstermill',
    '__dm_handle',
    '__dm_handle_kwargs',
    '__dm_json',
    '__dm_raise_from',
    '__dm_run_config',
    '__dm_run_config_kwargs',
    '__dm_solid_handle_kwargs',
    '__dm_sys',
]

INJECTED_BOILERPLATE = '''
# Injected parameters

import json as __dm_json
import sys as __dm_sys

import dagster as __dm_dagster
import dagster.cli.load_handle as __dm_dagster_cli_load_handle
import dagster.core.definitions.dependency as __dm_dagster_core_definitions_dependency
import dagstermill as __dm_dagstermill

# six.raise_from
if __dm_sys.version_info[:2] == (3, 2):
    exec("""def __dm_raise_from(value, from_value):
    try:
        if from_value is None:
            raise value
        raise value from from_value
    finally:
        value = None
""")
elif __dm_sys.version_info[:2] > (3, 2):
    exec("""def __dm_raise_from(value, from_value):
    try:
        raise value from from_value
    finally:
        value = None
""")
else:
    def __dm_raise_from(value, from_value):
        raise value

__dm_run_config = __dm_dagster.RunConfig(**__dm_json.loads('{dm_run_config_kwargs}'))

try:
    __dm_handle = __dm_dagster_cli_load_handle.handle_for_pipeline_cli_args(
        __dm_json.loads('{dm_handle_kwargs}'),
        use_default_repository_yaml=False,        
    )
except (__dm_dagster.check.CheckError, __dm_dagster_cli_load_handle.CliUsageError) as err:
    __dm_raise_from(
        __dm_dagstermill.DagstermillError(
            'Cannot invoke a dagstermill solid from an in-memory pipeline that was not loaded '
            'from an ExecutionTargetHandle. Run this pipeline using dagit, the dagster CLI, '
            'through dagster-graphql, or in-memory after loading it through an '
            'ExecutionTargetHandle.'
        ),
        err,
    )

__dm_solid_handle = __dm_dagster_core_definitions_dependency.SolidHandle.from_dict(
    __dm_json.loads('{dm_solid_handle_kwargs}')
)

context = __dm_dagstermill._reconstitute_pipeline_context(
    run_config=__dm_run_config,
    handle=__dm_handle,
    solid_handle=__dm_solid_handle,
    **__dm_json.loads('{dm_context}')
)
'''


class DagsterTranslator(papermill.translators.PythonTranslator):
    @classmethod
    def codify(cls, parameters):
        assert '__dm_context' in parameters
        assert '__dm_handle_kwargs' in parameters
        assert '__dm_run_config_kwargs' in parameters
        assert '__dm_solid_handle_kwargs' in parameters

        content = INJECTED_BOILERPLATE.format(
            dm_context=parameters['__dm_context'],
            dm_handle_kwargs=parameters['__dm_handle_kwargs'],
            dm_run_config_kwargs=parameters['__dm_run_config_kwargs'],
            dm_solid_handle_kwargs=parameters['__dm_solid_handle_kwargs'],
        )

        for name, val in parameters.items():
            if name in RESERVED_INPUT_NAMES:
                continue
            dm_unmarshal_call = '__dm_dagstermill._load_parameter("{name}", {val})'.format(
                name=name, val='"{val}"'.format(val=val) if isinstance(val, str) else val
            )
            content += '{}\n'.format(cls.assign(name, dm_unmarshal_call))

        return content


papermill.translators.papermill_translators.register('python', DagsterTranslator)

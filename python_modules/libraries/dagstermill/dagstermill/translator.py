import papermill

from dagster import seven

RESERVED_INPUT_NAMES = [
    '__dm_context',
    '__dm_dagstermill',
    '__dm_handle_kwargs',
    '__dm_json',
    '__dm_pipeline_run_dict',
    '__dm_solid_handle_kwargs',
    '__dm_solid_subset',
    '__dm_instance_ref_dict',
]

INJECTED_BOILERPLATE = '''
# Injected parameters
from dagster import seven as __dm_seven
import dagstermill as __dm_dagstermill
context = __dm_dagstermill._reconstitute_pipeline_context(**__dm_seven.json.loads('{pipeline_context_args}'))
'''


class DagsterTranslator(papermill.translators.PythonTranslator):
    @classmethod
    def codify(cls, parameters):
        assert '__dm_context' in parameters
        assert '__dm_handle_kwargs' in parameters
        assert '__dm_pipeline_run_dict' in parameters
        assert '__dm_solid_handle_kwargs' in parameters
        assert '__dm_solid_subset' in parameters
        assert '__dm_instance_ref_dict' in parameters

        context_args = parameters['__dm_context']
        pipeline_context_args = dict(
            handle_kwargs=parameters['__dm_handle_kwargs'],
            pipeline_run_dict=parameters['__dm_pipeline_run_dict'],
            solid_handle_kwargs=parameters['__dm_solid_handle_kwargs'],
            solid_subset=parameters['__dm_solid_subset'],
            instance_ref_dict=parameters['__dm_instance_ref_dict'],
            **context_args
        )

        content = INJECTED_BOILERPLATE.format(
            pipeline_context_args=seven.json.dumps(pipeline_context_args)
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

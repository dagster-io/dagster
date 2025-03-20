import papermill
import papermill.translators
from dagster_shared import seven

RESERVED_INPUT_NAMES = [
    "__dm_context",
    "__dm_dagstermill",
    "__dm_executable_dict",
    "__dm_json",
    "__dm_pipeline_run_dict",
    "__dm_node_handle_kwargs",
    "__dm_instance_ref_dict",
    "__dm_step_key",
    "__dm_input_names",
]

INJECTED_BOILERPLATE = """
# Injected parameters
from dagster_shared import seven as __dm_seven
import dagstermill as __dm_dagstermill
context = __dm_dagstermill._reconstitute_job_context(
    **{{
        key: __dm_seven.json.loads(value)
        for key, value
        in {job_context_args}.items()
    }}
)
"""


class DagsterTranslator(papermill.translators.PythonTranslator):
    @classmethod
    def codify(cls, parameters, comment=None):
        # comment is not used but is a required argument on newer versions of papermill
        assert "__dm_context" in parameters
        assert "__dm_executable_dict" in parameters
        assert "__dm_pipeline_run_dict" in parameters
        assert "__dm_node_handle_kwargs" in parameters
        assert "__dm_instance_ref_dict" in parameters
        assert "__dm_step_key" in parameters
        assert "__dm_input_names" in parameters

        context_args = parameters["__dm_context"]
        job_context_args = dict(
            executable_dict=parameters["__dm_executable_dict"],
            job_run_dict=parameters["__dm_pipeline_run_dict"],
            node_handle_kwargs=parameters["__dm_node_handle_kwargs"],
            instance_ref_dict=parameters["__dm_instance_ref_dict"],
            step_key=parameters["__dm_step_key"],
            **context_args,
        )

        for key in job_context_args:
            job_context_args[key] = seven.json.dumps(job_context_args[key])

        content = INJECTED_BOILERPLATE.format(job_context_args=job_context_args)

        for input_name in parameters["__dm_input_names"]:
            dm_load_input_call = f"__dm_dagstermill._load_input_parameter('{input_name}')"
            content += f"{cls.assign(input_name, dm_load_input_call)}\n"

        return content


papermill.translators.papermill_translators.register("python", DagsterTranslator)

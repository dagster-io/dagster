from dagster import op
from dagster._core.definitions.decorators.job_decorator import job
from numpy import full


@op(config_schema={"a_str": str, "an_int": int})
def op_with_config(context):
    print(f"str: {context.op_config['a_str']} int: {context.op_config['an_int']}")


@job
def job_with_config():
    op_with_config()


fully_satisified = op_with_config.configured(
    name="fully_satisfied", config_or_config_fn={"a_str": "configured value", "an_int": 3}
)


@job
def job_with_configured():
    fully_satisified()


# job_with_config.execute_in_process(
#     run_config={"ops": {"op_with_config": {"config": {"a_str": "value", "an_int": 4}}}}
# )

print(f"{fully_satisified.config_schema.parent_def.config_schema.as_field()}")
print(f"{fully_satisified.config_schema._passed_config}")

# job_with_configured.execute_in_process()

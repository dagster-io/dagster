from dagster import Field, InputDefinition, Int, List, configured, execute_pipeline, pipeline, solid


# start_configured_named
@solid(
    config_schema={
        "is_sample": Field(bool, is_required=False, default_value=False),
    },
    input_defs=[InputDefinition("xs", List[Int])],
)
def variance(context, xs):
    n = len(xs)
    mean = sum(xs) / n
    summed = sum((mean - x) ** 2 for x in xs)
    result = summed / (n - 1) if context.solid_config["is_sample"] else summed / n
    return result ** (1 / 2)


# If we want to use the same solid configured in multiple ways in the same pipeline,
# we have to specify unique names when configuring them:
sample_variance = configured(variance, name="sample_variance")({"is_sample": True})
population_variance = configured(variance, name="population_variance")({"is_sample": False})


@pipeline
def stats_pipeline():
    sample_variance()
    population_variance()


# end_configured_named


def run_pipeline():
    result = execute_pipeline(
        stats_pipeline,
        {
            "solids": {
                "sample_variance": {"inputs": {"xs": [4, 8, 15, 16, 23, 42]}},
                "population_variance": {
                    "inputs": {"xs": [33, 30, 27, 29, 32, 30, 27, 28, 30, 30, 30, 31]}
                },
            }
        },
    )
    return result

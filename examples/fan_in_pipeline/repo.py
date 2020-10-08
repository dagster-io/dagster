# start_repo_marker_0
from dagster import InputDefinition, List, OutputDefinition, pipeline, repository, solid


@solid(output_defs=[OutputDefinition(int)])
def return_one(_):
    return 1


@solid(input_defs=[InputDefinition("nums", List[int])], output_defs=[OutputDefinition(int)])
def sum_fan_in(_, nums):
    return sum(nums)


@pipeline
def fan_in_pipeline():
    fan_outs = []
    for i in range(0, 10):
        fan_outs.append(return_one.alias("return_one_{}".format(i))())
    sum_fan_in(fan_outs)


@repository
def fan_in_pipeline_repository():
    return [fan_in_pipeline]


# end_repo_marker_0

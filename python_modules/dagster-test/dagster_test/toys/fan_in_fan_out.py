from dagster import InputDefinition, List, OutputDefinition, pipeline, solid


@solid(output_defs=[OutputDefinition(int)])
def return_one(_):
    return 1


@solid(input_defs=[InputDefinition("num", int)])
def add_one_fan(_, num):
    return num + 1


@solid(input_defs=[InputDefinition("nums", List[int])])
def sum_fan_in(_, nums):
    return sum(nums)


def construct_fan_in_level(source, level, fanout):
    fan_outs = []
    for i in range(0, fanout):
        fan_outs.append(add_one_fan.alias("add_one_fan_{}_{}".format(level, i))(source))

    return sum_fan_in.alias("sum_{}".format(level))(fan_outs)


def construct_level_pipeline(name, levels, fanout):
    @pipeline(name=name)
    def _pipe():

        return_one_out = return_one()
        prev_level_out = return_one_out
        for level in range(0, levels):
            prev_level_out = construct_fan_in_level(prev_level_out, level, fanout)

    return _pipe


fan_in_fan_out_pipeline = construct_level_pipeline("fan_in_fan_out_pipeline", levels=10, fanout=50)

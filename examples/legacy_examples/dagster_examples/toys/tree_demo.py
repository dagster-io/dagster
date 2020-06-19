import time
from collections import defaultdict
from random import randint

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
)


def generate_solid(solid_id, num_outputs):
    def compute_fn(_context, _parent):
        time.sleep(float(randint(0, 100)) / 1000)
        for i in range(num_outputs):
            yield Output(i, 'out_{}'.format(i))

    return SolidDefinition(
        name=solid_id,
        input_defs=[InputDefinition(name='parent')],
        output_defs=[OutputDefinition(name='out_{}'.format(i)) for i in range(num_outputs)],
        compute_fn=compute_fn,
    )


def generate_tree(name, branch_factor, depth):
    """
    This function generates a pipeline definition which consists of solids that are arranged in a balanced tree.
    The compute functions in all of these solids sleep for a random interval and yield a integer to their corresponding
    outputs.

    Args:
        name (str): The name of the pipeline.
        branch_factor (int): the number of output branches for any non-leaf node.
        depth (int): depth of the tree.
    """
    check.str_param(name, 'name')
    check.int_param(branch_factor, 'branch_factor')
    check.int_param(depth, 'depth')

    node_counter = 0
    leaves = [generate_solid('{}_solid'.format(node_counter), branch_factor)]
    node_counter += 1
    level = 0
    deps = defaultdict(dict)
    solids = []
    while level != depth:
        num_iterations = branch_factor ** level
        for _ in range(num_iterations):
            solid_to_connect = leaves.pop()
            solids.append(solid_to_connect)
            for output in solid_to_connect.output_defs:
                new_output_solid = generate_solid('{}_solid'.format(node_counter), branch_factor)
                node_counter += 1
                deps[new_output_solid.name]['parent'] = DependencyDefinition(
                    solid_to_connect.name, output.name
                )
                leaves = [new_output_solid] + leaves
        level += 1
    solids += leaves
    return PipelineDefinition(name=name, solid_defs=solids, dependencies=deps)

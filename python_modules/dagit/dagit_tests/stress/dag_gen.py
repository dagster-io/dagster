import random
from collections import defaultdict

from dagster import DependencyDefinition, Field, In, OpDefinition, Out, Output
from dagster import _check as check
from dagster._legacy import PipelineDefinition


def generate_op(op_id, num_inputs, num_outputs, num_cfg):
    def compute_fn(_context, **_kwargs):
        for i in range(num_outputs):
            yield Output(i, "out_{}".format(i))

    config = {}
    for i in range(num_cfg):
        config[f"field_{i}"] = Field(str, is_required=False)

    return OpDefinition(
        name=op_id,
        ins={f"in_{i}": In(default_value="default") for i in range(num_inputs)},
        outs={f"out_{i}": Out() for i in range(num_outputs)},
        compute_fn=compute_fn,
        config_schema=config,
    )


def generate_pipeline(name, size, connect_factor=1.0):
    check.int_param(size, "size")
    check.invariant(size > 3, "Can not create pipelines with less than 3 nodes")
    check.float_param(connect_factor, "connect_factor")

    random.seed(name)

    # generate nodes
    ops = {}
    for i in range(size):
        num_inputs = random.randint(1, 3)
        num_outputs = random.randint(1, 3)
        num_cfg = random.randint(0, 5)
        op_id = "{}_op_{}".format(name, i)
        ops[op_id] = generate_op(
            op_id=op_id,
            num_inputs=num_inputs,
            num_outputs=num_outputs,
            num_cfg=num_cfg,
        )

    op_ids = list(ops.keys())
    # connections
    deps = defaultdict(dict)
    for i in range(int(size * connect_factor)):
        # choose output
        out_idx = random.randint(0, len(op_ids) - 2)
        out_op_id = op_ids[out_idx]
        output_op = ops[out_op_id]
        output_name = output_op.output_defs[random.randint(0, len(output_op.output_defs) - 1)].name

        # choose input
        in_idx = random.randint(out_idx + 1, len(op_ids) - 1)
        in_op_id = op_ids[in_idx]
        input_op = ops[in_op_id]
        input_name = input_op.ins[random.randint(0, len(input_op.ins) - 1)].name

        # map
        deps[in_op_id][input_name] = DependencyDefinition(out_op_id, output_name)

    return PipelineDefinition(name=name, solid_defs=list(ops.values()), dependencies=deps)

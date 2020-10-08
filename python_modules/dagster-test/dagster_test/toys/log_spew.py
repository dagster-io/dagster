import time

from dagster import InputDefinition, Output, OutputDefinition, pipeline, solid


def nonce_solid(name, n_inputs, n_outputs):
    """Creates a solid with the given number of (meaningless) inputs and outputs.

    Config controls the behavior of the nonce solid."""

    @solid(
        name=name,
        input_defs=[InputDefinition(name="input_{}".format(i)) for i in range(n_inputs)],
        output_defs=[OutputDefinition(name="output_{}".format(i)) for i in range(n_outputs)],
    )
    def solid_fn(context, **_kwargs):
        for i in range(200):
            time.sleep(0.02)
            if i % 1000 == 420:
                context.log.error("Error message seq={i} from solid {name}".format(i=i, name=name))
            elif i % 100 == 0:
                context.log.warning(
                    "Warning message seq={i} from solid {name}".format(i=i, name=name)
                )
            elif i % 10 == 0:
                context.log.info("Info message seq={i} from solid {name}".format(i=i, name=name))
            else:
                context.log.debug("Debug message seq={i} from solid {name}".format(i=i, name=name))
        for i in range(n_outputs):
            yield Output(value="foo", output_name="output_{}".format(i))

    return solid_fn


@pipeline(
    description="Demo pipeline that spits out different types of log messages to the event log."
)
def log_spew():
    one_in_one_out = nonce_solid("one_in_one_out", 1, 1)
    two_in_one_out = nonce_solid("two_in_one_out", 2, 1)

    solid_a = nonce_solid("no_in_two_out", 0, 2).alias("solid_a")
    solid_b = one_in_one_out.alias("solid_b")
    solid_c = nonce_solid("one_in_two_out", 1, 2).alias("solid_c")
    solid_d = two_in_one_out.alias("solid_d")
    solid_e = one_in_one_out.alias("solid_e")
    solid_f = two_in_one_out.alias("solid_f")
    solid_g = nonce_solid("one_in_none_out", 1, 0).alias("solid_g")

    a_0, a_1 = solid_a()
    b = solid_b(input_0=a_0)
    c_0, _c_1 = solid_c(input_0=a_1)
    d = solid_d(input_0=b, input_1=c_0)
    e = solid_e(input_0=c_0)
    f = solid_f(input_0=d, input_1=e)
    solid_g(input_0=f)

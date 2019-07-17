# pylint: disable=no-value-for-parameter

from dagster import composite_solid, pipeline, solid, Field, Int, String


@solid(config={'foo': Field(String)})
def basic(context):
    return context.solid_config


def inner_wrap_fn(_ctx, cfg):
    return {
        'basic': {
            'config': {'foo': 'override here' + cfg['inner_first'] + ' : ' + cfg['inner_second']}
        }
    }


@composite_solid(
    config_fn=inner_wrap_fn, config={'inner_first': Field(String), 'inner_second': Field(String)}
)
def inner_wrap():
    return basic()


def outer_wrap_fn(_ctx, cfg):
    return {
        'inner_wrap': {
            'config': {'inner_first': cfg['outer_first'], 'inner_second': cfg['outer_second']}
        }
    }


@composite_solid(
    config_fn=outer_wrap_fn,
    config={'outer_first': Field(String), 'outer_second': Field(String), 'outer_third': Field(Int)},
)
def outer_wrap():
    return inner_wrap()


@pipeline(name='config_mapping')
def config_mapping_pipeline():
    return outer_wrap()

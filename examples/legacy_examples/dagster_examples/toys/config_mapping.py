from dagster import Field, Int, String, composite_solid, pipeline, solid


@solid(config_schema={'foo': Field(String)})
def basic(context):
    return context.solid_config


def inner_wrap_fn(cfg):
    return {
        'basic': {
            'config': {'foo': 'override here' + cfg['inner_first'] + ' : ' + cfg['inner_second']}
        }
    }


@composite_solid(
    config_fn=inner_wrap_fn,
    config_schema={'inner_first': Field(String), 'inner_second': Field(String)},
)
def inner_wrap():
    return basic()


def outer_wrap_fn(cfg):
    return {
        'inner_wrap': {
            'config': {'inner_first': cfg['outer_first'], 'inner_second': cfg['outer_second']}
        }
    }


@composite_solid(
    config_fn=outer_wrap_fn,
    config_schema={'outer_first': Field(String), 'outer_second': Field(String), 'outer_third': Int},
)
def outer_wrap():
    return inner_wrap()


@pipeline(name='config_mapping')
def config_mapping_pipeline():
    return outer_wrap()

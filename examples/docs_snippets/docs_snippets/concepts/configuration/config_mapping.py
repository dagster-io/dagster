from dagster import Field, Shape, composite_solid, pipeline, repository, seven, solid


@solid(
    config_schema={
        "cluster_cfg": Shape(
            {
                "num_mappers": Field(int),
                "num_reducers": Field(int),
                "master_heap_size_mb": Field(int),
                "worker_heap_size_mb": Field(int),
            }
        ),
        "name": Field(str),
    }
)
def hello(context):
    context.log.info(seven.json.dumps(context.solid_config["cluster_cfg"]))
    return "Hello, %s!" % context.solid_config["name"]


def config_mapping_fn(cfg):
    return {
        "hello": {
            "config": {
                "cluster_cfg": {
                    "num_mappers": 100,
                    "num_reducers": 20,
                    "master_heap_size_mb": 1024,
                    "worker_heap_size_mb": 8192,
                },
                "name": cfg["name"],
            }
        }
    }


@composite_solid(
    config_fn=config_mapping_fn,
    config_schema={"name": Field(str, is_required=False, default_value="Sam")},
)
def hello_external():
    return hello()


@pipeline
def example_pipeline():
    hello_external()


@repository
def config_mapping():
    return [example_pipeline]

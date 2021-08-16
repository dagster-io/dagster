from dagster import (
    InputDefinition,
    dagster_type_loader,
    execute_pipeline,
    pipeline,
    solid,
    usable_as_dagster_type,
)


# def_start_marker
@dagster_type_loader(config_schema={"diameter": float, "juiciness": float, "cultivar": str})
def apple_loader(_context, config):
    return Apple(
        diameter=config["diameter"], juiciness=config["juiciness"], cultivar=config["cultivar"]
    )


@usable_as_dagster_type(loader=apple_loader)
class Apple:
    def __init__(self, diameter, juiciness, cultivar):
        self.diameter = diameter
        self.juiciness = juiciness
        self.cultivar = cultivar


@solid(input_defs=[InputDefinition("input_apple", Apple)])
def my_solid(context, input_apple):
    context.log.info(f"input apple diameter: {input_apple.diameter}")


@pipeline
def my_pipeline():
    my_solid()


# def_end_marker


def execute_with_config():
    # execute_start_marker
    execute_pipeline(
        my_pipeline,
        run_config={
            "solids": {
                "my_solid": {
                    "inputs": {
                        "input_apple": {"diameter": 2.4, "juiciness": 6.0, "cultivar": "honeycrisp"}
                    }
                }
            }
        },
    )
    # execute_end_marker

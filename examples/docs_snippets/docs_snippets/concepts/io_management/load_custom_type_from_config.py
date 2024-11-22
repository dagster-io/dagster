# def_start_marker
from typing import Dict, Union

from dagster import (
    DagsterTypeLoaderContext,
    OpExecutionContext,
    dagster_type_loader,
    job,
    op,
    usable_as_dagster_type,
)


@dagster_type_loader(
    config_schema={"diameter": float, "juiciness": float, "cultivar": str}
)
def apple_loader(
    _context: DagsterTypeLoaderContext, config: dict[str, Union[float, str]]
):
    return Apple(
        diameter=config["diameter"],
        juiciness=config["juiciness"],
        cultivar=config["cultivar"],
    )


@usable_as_dagster_type(loader=apple_loader)
class Apple:
    def __init__(self, diameter, juiciness, cultivar):
        self.diameter = diameter
        self.juiciness = juiciness
        self.cultivar = cultivar


@op
def my_op(context: OpExecutionContext, input_apple: Apple):
    context.log.info(f"input apple diameter: {input_apple.diameter}")


@job
def my_job():
    my_op()


# def_end_marker


def execute_with_config():
    # execute_start_marker
    my_job.execute_in_process(
        run_config={
            "ops": {
                "my_op": {
                    "inputs": {
                        "input_apple": {
                            "diameter": 2.4,
                            "juiciness": 6.0,
                            "cultivar": "honeycrisp",
                        }
                    }
                }
            }
        },
    )
    # execute_end_marker

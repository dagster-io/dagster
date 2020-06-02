from dagster_examples.toys.composition import composition
from dagster_examples.toys.config_mapping import config_mapping_pipeline
from dagster_examples.toys.error_monster import error_monster
from dagster_examples.toys.fan_in_fan_out import fan_in_fan_out_pipeline
from dagster_examples.toys.hammer import hammer_pipeline
from dagster_examples.toys.log_demo import hello_error_pipeline, hello_logs_pipeline
from dagster_examples.toys.log_spew import log_spew
from dagster_examples.toys.many_events import many_events
from dagster_examples.toys.resources_error import resource_error_pipeline
from dagster_examples.toys.sleepy import sleepy_pipeline
from dagster_examples.toys.solid_aliasing_def_collisions import solid_aliasing_def_collisions
from dagster_examples.toys.tree_demo import generate_tree

from dagster import repository


@repository
def toys_repository():
    return [
        composition,
        config_mapping_pipeline,
        error_monster,
        fan_in_fan_out_pipeline,
        hammer_pipeline,
        hello_error_pipeline,
        hello_logs_pipeline,
        log_spew,
        many_events,
        resource_error_pipeline,
        sleepy_pipeline,
        solid_aliasing_def_collisions,
        generate_tree('demo_tree_pipeline', 2, 3),
    ]

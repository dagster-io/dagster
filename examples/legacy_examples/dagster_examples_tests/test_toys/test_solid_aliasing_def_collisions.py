from dagster_examples.toys.solid_aliasing_def_collisions import solid_aliasing_def_collisions

from dagster import execute_pipeline


def test_smoke_solid_aliasing_def_collisions():
    assert execute_pipeline(solid_aliasing_def_collisions).success

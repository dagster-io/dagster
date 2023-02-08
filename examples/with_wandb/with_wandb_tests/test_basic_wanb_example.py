from with_wandb.repository import dagster_with_wandb


def test_can_load():
    assert dagster_with_wandb.get_job("simple_job_example")

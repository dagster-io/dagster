"""evaluation_daily_schedule wiring tests (Point 8).

The sensor is exercised in test_sensor.py; this closes the other half of Point 8
by asserting the periodic schedule is wired to the evaluation job on the expected
cadence.
"""

from ragas_evaluation_pipeline.schedules import evaluation_daily_schedule


def test_schedule_runs_daily_at_9am():
    assert evaluation_daily_schedule.cron_schedule == "0 9 * * *"


def test_schedule_targets_the_evaluation_job():
    assert evaluation_daily_schedule.job.name == "evaluation_job"

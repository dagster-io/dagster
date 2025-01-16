---
title: Configuring job behavior based on scheduled run time
sidebar_position: 200
---

This example demonstrates how to use run config to vary the behavior of a job based on its scheduled run time.

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/schedules/schedules.py startafter=start_run_config_schedule endbefore=end_run_config_schedule
@op(config_schema={"scheduled_date": str})
def configurable_op(context: OpExecutionContext):
    context.log.info(context.op_config["scheduled_date"])


@job
def configurable_job():
    configurable_op()


@schedule(job=configurable_job, cron_schedule="0 0 * * *")
def configurable_job_schedule(context: ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {"configurable_op": {"config": {"scheduled_date": scheduled_date}}}
        },
        tags={"date": scheduled_date},
    )
```

| Notes | Related docs | APIs in this example |
|-------|--------------|----------------------|
|       | [Op jobs](/todo) | <PyObject section="ops" module="dagster" object="op" decorator />, <PyObject section="jobs" module="dagster" object="job" decorator />, <PyObject section="execution" module="dagster" object="OpExecutionContext" />, <PyObject section="schedules-sensors" object="ScheduleEvaluationContext" />, <PyObject section="schedules-sensors" module="dagster" object="RunRequest" /> |

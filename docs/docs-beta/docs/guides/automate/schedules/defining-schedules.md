---
title: Defining schedules
sidebar_position: 100
---

## Defining basic schedules

The following examples demonstrate how to define some basic schedules.

<Tabs>
  <TabItem name="Using ScheduleDefinition">

This example demonstrates how to define a schedule using <PyObject object="ScheduleDefinition" /> that will run a job every day at midnight. While this example uses [op jobs](/concepts/ops-jobs-graphs/jobs) (<PyObject object="job" decorator />), the same approach will work with [asset jobs](/concepts/assets/asset-jobs) (<PyObject object="define_asset_job" />).

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/schedules/schedules.py startafter=start_basic_schedule endbefore=end_basic_schedule
@job
def my_job(): ...


basic_schedule = ScheduleDefinition(job=my_job, cron_schedule="0 0 * * *")
```

<table
  className="table"
  style={{
    width: "100%",
  }}
>
  <tbody>
    <tr>
      <td
        style={{
          width: "20%",
        }}
      >
        <strong>Notes</strong>
      </td>
      <td>
        The <code>cron_schedule</code> argument accepts standard{" "}
        <a href="https://en.wikipedia.org/wiki/Cron">cron expressions</a>. If
        your <code>croniter</code> dependency's version is{" "}
        <code>>= 1.0.12</code>, the argument will also accept the following:
        <ul>
          <li>
            <code>@daily</code>
          </li>
          <li>
            <code>@hourly</code>
          </li>
          <li>
            <code>@monthly</code>
          </li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>
        <strong>Related docs</strong>
      </td>
      <td>
        <ul>
          <li>
            <a href="/concepts/assets/asset-jobs">Asset jobs</a>
          </li>
          <li>
            <a href="/concepts/automation/schedules/automating-assets-schedules-jobs">
              Automating assets using jobs and schedules
            </a>
          </li>
          <li>
            <a href="/concepts/ops-jobs-graphs/jobs">Op jobs</a>
          </li>
          <li>
            <a href="/concepts/automation/schedules/automating-ops-schedules-jobs">
              Automating ops using jobs and schedules
            </a>
          </li>
          <li>
            <a href="https://en.wikipedia.org/wiki/Cron" target="_blank">
              Cron expressions
            </a>
          </li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>
        <strong>APIs in this example</strong>
      </td>
      <td>
        <PyObject object="job" decorator />,{" "}
        <PyObject object="ScheduleDefinition" />
      </td>
    </tr>
  </tbody>
</table>

</TabItem>
<TabItem name="Using @schedule">

This example demonstrates how to define a schedule using <PyObject object="schedule" decorator />, which provides more flexibility than <PyObject object="ScheduleDefinition" />. For example, you can [configure job behavior based on its scheduled run time](#configuring-job-behavior-based-on-scheduled-run-time) or [emit log messages](#emitting-log-messages-from-schedule-evaluations).

```python
@schedule(job=my_job, cron_schedule="0 0 * * *")
def basic_schedule(): ...
  # things the schedule does, like returning a RunRequest or SkipReason
```

<table
  className="table"
  style={{
    width: "100%",
  }}
>
  <tbody>
    <tr>
      <td
        style={{
          width: "20%",
        }}
      >
        <strong>Notes</strong>
      </td>
      <td>
        The decorator's <code>cron_schedule</code> argument accepts standard{" "}
        <a href="https://en.wikipedia.org/wiki/Cron">cron expressions</a>. If
        your <code>croniter</code> dependency's version is{" "}
        <code>>= 1.0.12</code>, the argument will also accept the following:
        <ul>
          <li>
            <code>@daily</code>
          </li>
          <li>
            <code>@hourly</code>
          </li>
          <li>
            <code>@monthly</code>
          </li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>
        <strong>Related docs</strong>
      </td>
      <td>
        <ul>
          <li>
            <a href="/concepts/assets/asset-jobs">Asset jobs</a>
          </li>
          <li>
            <a href="/concepts/automation/schedules/automating-assets-schedules-jobs">
              Automating assets using jobs and schedules
            </a>
          </li>
          <li>
            <a href="/concepts/ops-jobs-graphs/jobs">Op jobs</a>
          </li>
          <li>
            <a href="/concepts/automation/schedules/automating-ops-schedules-jobs">
              Automating ops using jobs and schedules
            </a>
          </li>
          <li>
            <a href="https://en.wikipedia.org/wiki/Cron" target="_blank">
              Cron expressions
            </a>
          </li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>
        <strong>APIs in this example</strong>
      </td>
      <td>
        <PyObject object="schedule" decorator />,{" "}
        <PyObject object="ScheduleDefinition" />
      </td>
    </tr>
  </tbody>
</table>

</TabItem>
</Tabs>

## Emitting log messages from schedule evaluation

This example demonstrates how to emit log messages from a schedule during its evaluation function. These logs will be visible in the UI when you inspect a tick in the schedule's tick history.

```python file=concepts/partitions_schedules_sensors/schedules/schedules.py startafter=start_schedule_logging endbefore=end_schedule_logging
@schedule(job=my_job, cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a schedule!")
    return SkipReason("Nothing to do")
```

<table
  className="table"
  style={{
    width: "100%",
  }}
>
  <tbody>
    <tr>
      <td
        style={{
          width: "20%",
        }}
      >
        <strong>Notes</strong>
      </td>
      <td>
        Schedule logs are stored in your{" "}
        <a href="/deployment/dagster-instance#compute-log-storage">
          Dagster instance's compute log storage
        </a>
        . You should ensure that your compute log storage is configured to view your
        schedule logs.
      </td>
    </tr>
    <tr>
      <td>
        <strong>Related docs</strong>
      </td>
      <td>
        <ul>
          <li>
            <a href="/concepts/logging">Logging</a>
          </li>
          <li>
            <a href="/deployment/dagster-instance#compute-log-storage">
              Dagster instance - Compute log storage
            </a>
          </li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>
        <strong>APIs in this example</strong>
      </td>
      <td>
        <PyObject object="schedule" decorator />,{" "}
        <PyObject object="ScheduleDefinition" />,{" "}
        <PyObject object="SkipReason" />
      </td>
    </tr>
  </tbody>
</table>

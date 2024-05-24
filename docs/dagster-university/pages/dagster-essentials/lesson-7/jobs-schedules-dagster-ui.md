---
title: 'Lesson 7: Jobs and schedules in the Dagster UI'
module: 'dagster_essentials'
lesson: '7'
---

# Jobs and schedules in the Dagster UI

Like other Dagster definitions, jobs and schedules can be viewed and managed in the Dagster UI. The UI contains information about where the jobs and schedules are used, as well as the ability to toggle them on and off.

In addition to viewing and managing jobs and schedules in the UI, running `dagster dev` also spins up the `dagster-daemon`. The `dagster-daemon` is a long-running process that does things like check the time to see if a schedule should be run or if a sensor should be ticked, which we’ll cover more in a later lesson.

To ensure the jobs and schedules are visible, **reload the definitions** before continuing.

---

## Jobs in the UI

{% table %}

- Accessing jobs

---

- {% width="60%" %}
  To view the jobs in the UI, you can:

  - Click **Overview > Jobs**, or
  - Click **Deployment**, then click on a code location. Click the **Jobs tab**.

  The table in the **Jobs** tab contains the following info:

  - **Name** - The name of the job
  - **Schedules/sensors** - The schedules and/or sensors attached to the job, including whether they’re enabled
  - **Latest run** - When the job last ran
  - **Run history** - Historical information about the job’s runs

- ![The Jobs tab in the Dagster UI](/images/dagster-essentials/lesson-7/ui-jobs-tab.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Viewing a job's assets

---

- {% width="60%" %}
  By selecting a specific job, you will be able to see the asset graph containing the job's assets.

- ![The asset graph for the trip_update_job in the Dagster UI](/images/dagster-essentials/lesson-7/ui-trip-update-job-asset-graph.png) {% rowspan=2 %}

{% /table %}

---

## Schedules in the UI

{% table %}

- Accessing schedules

---

- {% width="60%" %}
  To view the schedules in the UI, you can:

  - Click **Overview > Schedules**, or
  - Click **Deployment**, then click on a code location. Click the **Schedules tab**.

  The table in the **Schedules tab** contains the following info:

  - **Schedule name -** The name of the schedule
  - **Schedule -** The frequency of the schedule
  - **Running -** Whether the schedule is currently on or off
  - **Last tick -** When the schedule was last started
  - **Last run -** When the schedule was last run

- ![The Schedules tab in the Dagster UI](/images/dagster-essentials/lesson-7/ui-schedules-tab.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Viewing schedule details

---

- {% width="60%" %}
  To view historical information about a schedule, click a schedule in the **Schedules** tab. The **Schedule details** page contains a view of the schedule’s tick and run history.

- ![The Schedule details page in the Dagster UI](/images/dagster-essentials/lesson-7/ui-schedule-details.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Starting and stopping schedules

---

- {% width="60%" %}
  To start or stop a schedule, use the **toggle next to the schedule’s name** in the upper-left corner of the page. When the schedule is on, its **Next tick** will also be visible.

- ![An enabled schedule in the Schedule details page](/images/dagster-essentials/lesson-7/ui-enabled-schedule.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Testing schedules

---

- {% width="60%" %}
  To test a schedule, use the **Test Schedule** button in the upper-right corner of the page. This can be handy when a schedule doesn’t run very often or you want to make sure a schedule is working correctly.

- ![The Test Schedule button highlighted in the Schedule details page](/images/dagster-essentials/lesson-7/ui-test-schedule.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Selecting a mock evaluation time

---

- {% width="60%" %}
  After the button is clicked, you’ll be prompted to select a mock evaluation time.

  Click **Evaluate** to run the test.

- ![Mock evaluation time selection](/images/dagster-essentials/lesson-7/ui-mock-evaluation-time.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Viewing schedule test results

---

- {% width="60%" %}
  After the test completes, the results of the evaluation will be displayed.

- ![Schedule test results](/images/dagster-essentials/lesson-7/ui-schedule-test-results.png) {% rowspan=2 %}

{% /table %}

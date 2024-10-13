---
title: 'Lesson 3: Troubleshooting failed runs'
module: 'dagster_essentials'
lesson: '3'
---

# Troubleshooting failed runs

Now that you’re familiar with how assets are materialized and where to find details about their execution, let’s focus on how to troubleshoot issues. To demonstrate how to troubleshoot, you’ll intentionally cause the `taxi_trips_file` asset to fail.

In the `assets/trips.py` file, comment out the `from . import constants` line so it looks like this:

```python
import requests
# from . import constants # <---- Import commented out here
from dagster import asset

@asset
def taxi_trips_file() -> None:
    """
      The raw parquet files for the taxi trips dataset. Sourced from the NYC Open Data portal.
    """
    month_to_fetch = '2023-03'
    raw_trips = requests.get(
        f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month_to_fetch}.parquet"
    )

    with open(constants.TAXI_TRIPS_TEMPLATE_FILE_PATH.format(month_to_fetch), "wb") as output_file:
        output_file.write(raw_trips.content)
```

In the Dagster UI, navigate to the **Global asset lineage** page and click Materialize again to try materializing the `taxi_trips_file` asset. As expected, the run will fail, resulting in the asset looking like this in the graph:

![Failed taxi_trips_file asset](/images/dagster-essentials/lesson-3/failed-asset.png)

Click the **date** in the asset to open the **Run details** page again. As you can see, it looks quite a bit different from the happy green success we saw before:

![Run details page showing a run failure](/images/dagster-essentials/lesson-3/failed-run-details-page.png)

When a run results in an error, the Run details page will indicate that something went wrong by:

- Displaying a **Failure** status in the **Run stats**
- Highlighting the problem step (or steps) in the **Run timeline** in red
- Listing the problem step(s) in the **Errored** section next to the **Run timeline**
- Displaying detailed error information about the problem step(s) in the **Run logs**

To hone in on what went wrong, let’s take a closer look at the logs. We’ll use the **structured view** of the logs for this example.

---

## Using logs to troubleshoot

{% table %}

- Step one

---

- {% width="60%" %}
  In the logs, locate the step that failed by looking for a STEP_FAILURE event. We’ve highlighted the problem step in the image to the right.

- ![Highlighted STEP_FAILURE event in the Run logs](/images/dagster-essentials/lesson-3/run-failure-step.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step two

---

- {% width="60%" %}
  In the **INFO** column for the failed step, click the View full message button to display the full stacktrace. A popover window like the one to the right will display.

  At this point, you can use the stacktrace to identify and fix the cause of the error. In this case, it’s because we didn’t import `constants`, leaving it undefined.

  To fix this, uncomment the `from . import constants` line in the `trips.py` file and save it.

  In the Dagster UI, click **OK** to close the popover window from the run logs.

- ![Full stacktrace error displayed in the Dagster UI after clicking  View full message in the Run logs](/images/dagster-essentials/lesson-3/stacktrace-error.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step three

---

- {% width="60%" %}
  After adding the import back in and saving the `trips.py` file, you’ll re-execute the run.

  In the Run details page, locate and click the **Re-execute all (\*)** button near the top-right corner of the page. This will re-execute all the steps in the run.

- ![Highlighted Re-execute all button in the Run details page, located near the top-right corner](/images/dagster-essentials/lesson-3/highlighted-re-execute.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step four

---

- {% width="60%" %}
  At this point, the run should successfully materialize the asset!

  The Run details page will look similar to the image on the right, indicating that while the root (original) run failed, the re-execution was successful.

- ![Successful run details page after the re-execution](/images/dagster-essentials/lesson-3/re-execute-successful.png) {% rowspan=2 %}

{% /table %}

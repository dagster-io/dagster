---
title: 'Lesson 9: Sensors in the Dagster UI'
module: 'dagster_essentials'
lesson: '9'
---

# Sensors in the Dagster UI

Now that the sensor is built, let's take a look around the Dagster UI.

{% table %}

- Step one

---

- {% width="60%" %}
  Navigate to the **Global Asset Lineage** page, where you should see the new asset, `adhoc_request`.

  **Note:** If you don’t see the asset, click **Reload definitions** first.

- ![The new adhoc_request asset in the Dagster UI](/images/dagster-essentials/lesson-9/ui-asset-lineage-with-sensors.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step two

---

- {% width="60%" %}
  Click **Overview > Sensors**. In this tab, you’ll see the `adhoc_request_sensor`.

  Notice that the **Running** toggle button has the sensor marked as turned off. By default, all sensors and schedules are off when first loaded.

- ![The Sensors tab in the Dagster UI](/images/dagster-essentials/lesson-9/ui-sensors-tab.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step three

---

- {% width="60%" %}
  Click `adhoc_request_sensor` to open the **Sensor details** page.

  On this page, you’ll find detailed information about the sensor including the jobs that use it, its tick and run history, and more.

- ![The Sensor details tab in the Dagster UI](/images/dagster-essentials/lesson-9/ui-sensor-details.png) {% rowspan=2 %}

{% /table %}

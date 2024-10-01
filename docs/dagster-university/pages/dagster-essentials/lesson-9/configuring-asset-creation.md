---
title: 'Lesson 9: Configuring asset creation'
module: 'dagster_essentials'
lesson: '9'
---

# Configuring asset creation

Configuring asset creation is not specific to sensors, but when materializing assets, you may want to customize some parts of the logic depending on how it’s run. For example, you may want to customize an email to address the reader by their name and send it to their address.

In this context, you will want to customize the asset materialization based on the borough and date range that the stakeholder requested.

These configurations are most commonly added at the run-level and can be passed into schedules and sensors. In addition, runs can be customized in the Dagster UI when manually launching runs.

Let’s write a new configuration that we can use to customize the asset materialization.

1. In the `assets` directory, create a `requests.py` file.

2. Add the following import to the top of the file:

   ```bash
   from dagster import Config
   ```

   This is used as the base class when making custom configurations.

3. Next, define a new subclass called `AdhocRequestsConfig` that takes in the following `str` attributes:
   - `filename`: the name of the request’s JSON file
   - `borough`: the New York City borough to be analyzed. The value should be one of `Manhattan`, `Brooklyn`, `Queens`, `Bronx`, or `Staten Island`
   - `start_date`: The beginning of the date range of the request, in the format `YYYY-MM-DD`
   - `end_date`: The end of the date range of the request, in the format `YYYY-MM-DD`

The `requests.py` file should look like the code snippet below:

```python
from dagster import Config

class AdhocRequestConfig(Config):
    filename: str
    borough: str
    start_date: str
    end_date: str
```

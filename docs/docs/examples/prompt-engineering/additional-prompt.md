---
title: Additional Prompt
description: Using an additional prompt
last_update:
  author: Dennis Hume
sidebar_position: 50
---

For our final prompt engineering asset, we can reuse many of the concepts we have already learned. We can start with the prompt itself. Unlike the original prompt, which would come in from the user, we can be very specific with the input value for the additional prompt. In this case, we will provide the current time (we can ignore timezones for this example) and the hours of operation from the fuel station. As with the last prompt, we will also ensure the output is in JSON. To accomplish this, our additional prompt might look like:

<CodeExample
  path="docs_projects/project_prompt_eng/project_prompt_eng/assets.py"
  language="python"
  startAfter="start_fuel_station_prompt"
  endBefore="end_fuel_station_prompt"
/>

Now that we have the prompt, we can create our asset. The asset will combine the current time with the alternative fuel stations data. It will then generate a prompt for each fuel station to ask the AI model and determine if the fuel station is currently available.

<CodeExample
  path="docs_projects/project_prompt_eng/project_prompt_eng/assets.py"
  language="python"
  startAfter="start_available_fuel_stations"
  endBefore="end_available_fuel_stations"
/>

## Running the pipeline

With all the pieces in place, we can execute our full pipeline. The prompts at each step will ensure that all the assets exchange data correctly. We can use the parsed down input from before: "I'm near the The Art Institute of Chicago and driving a Kia EV9". This input can be supplied at execution within the run launcher -- just set the configuration for the `user_input_prompt` asset:

```yaml
ops:
  user_input_prompt:
    config:
      location: I'm near the The Art Institute of Chicago and driving a Kia EV9
```

After the assets have all materialized, you can view the results in the logs of the `available_fuel_stations` asset:

```
INTERPARK ADAMWABASH 1 at 17 E Adams St is 0.16458 miles away
INTERPARK ADAMWABASH 2 at 17 E Adams St is 0.16613 miles away
MILLENNIUM GRGS MPG STATION #3 at 5 S Columbus Dr is 0.23195 miles away
```

---
title: Additional Prompt
description: Using an additional prompt
last_update:
  author: Dennis Hume
sidebar_position: 40
---

For our final prompt engineering asset. We can reuse many of the concepts we have already learned. We can start with the prompt itself. Unlike the original prompt which would come in from the user, we can be very specific with the input value for the prompt. In this case we will provide the current time (we can ignore timezones for now) and the hours of operation from the fuel station. And like the last prompt to make parsing easier, we can ensure the output is in JSON format. To do this a prompt may look something like:

<CodeExample path="project_prompt_eng/project_prompt_eng/assets.py" language="python" lineStart="32" lineEnd="63"/>

Now that we have the prompt we can create our asset. The asset will record the current time and combine that with the alternative fuel stations it recieved from the last asset. It will then use combine that information as our input to supply into the prompt which we will use to ask our AI model. In this case it will iterate through the sample of fuel stations and tell the user if they are currently open and how far they are away from their current location.

<CodeExample path="project_prompt_eng/project_prompt_eng/assets.py" language="python" lineStart="117" lineEnd="154"/>

## Running the Pipeline
With all the pieces in place we execute our pipeline. The prompts will ensure that all the assets can exchange data as expected. And the user input does not need to be overly detailed. We can use the parsed down prompt from before: "I'm near the The Art Institute of Chicago and driving a Kia EV9". To execute the pipeline this way, simply set that for the configuration for the `user_input_prompt` asset.

```yaml
ops:
  user_input_prompt:
    config:
        location: I'm near the The Art Institute of Chicago and driving a Kia EV9
```

After the assets have all materialized you can view the results in the logs of the `fuel_station_available` asset:

```
INTERPARK ADAMWABASH 1 at 17 E Adams St is 0.16458 miles away
INTERPARK ADAMWABASH 2 at 17 E Adams St is 0.16613 miles away
MILLENNIUM GRGS MPG STATION #3 at 5 S Columbus Dr is 0.23195 miles away
```
---
title: Prompts
description: Generating the first prompt
last_update:
  author: Dennis Hume
sidebar_position: 20
---

We will be working with the API for the National Renewable Energy Laboratory ([NREL](https://www.nrel.gov/)). This API allows us to find nearby alternative fuel stations. To use this API, we need to provide our latitude and longitude and some information about our vehicle. Trying to make this user friendly, we might want to put an AI in front to translate free text into the information we need.

Using AI models like Claude, we can get coordinates based on an address as well as parse information out on our vehicle. For example if we told it: "I'm near the The Art Institute of Chicago and driving a Kia EV9, what are my coordinates and my vehicle type?", it will provide an answer that may sound like this:

> Your coordinates will depend on your exact location near The Art Institute of Chicago, but its approximate coordinates are 41.8796° N, 87.6237° W. If you're nearby, your latitude and longitude should be close to these.
>
> Your vehicle type is a Kia EV9, which is a fully electric SUV. Let me know if you need parking suggestions or other assistance nearby!

This is helpful, but has a couple of issues. First, it requires the user to know what to include for our backend API. We don't want to count on the user to include that information. Also, the response we get back will be hard to parse, and we cannot guarantee that it will always be in the same format.

## Prompts

To get around this, we can employ prompt engineering. Prompt engineering is the process of crafting effective prompts to guide AI models toward generating accurate, relevant, or desired outputs. When including the output of AI models in data pipelines, one of the most important things is to ensure the output is in a format we expect. In this case, we know the information we want back from the AI model. Instead of a free text response, it would be helpful to have something easier to parse, like JSON, only containing the fields we need to make the API call.

We can write a prompt that tells the models our desired outcome and provide an example. In our case, a prompt might look like this:

<CodeExample
  path="docs_projects/project_prompt_eng/project_prompt_eng/assets.py"
  language="python"
  startAfter="start_location_prompt"
  endBefore="end_location_prompt"
/>

Now we can use this prompt with Claude. Within our Dagster asset (`user_input_prompt`) we can use the `AnthropicResource` to easily interact with the Anthropic client. We will also want to include a [run configuration](/guides/operate/configuration/run-configuration) for the asset so we can reuse this same pipeline with slightly different inputs. Finally, since we can ensure the response format from Claude with our prompt engineering, we can define a more specific output for the asset. Using [Pydantic](https://docs.pydantic.dev/latest/), we can define the exact schema we expect.

<CodeExample
  path="docs_projects/project_prompt_eng/project_prompt_eng/assets.py"
  language="python"
  startAfter="start_user_input_prompt"
  endBefore="end_user_input_prompt"
/>

Looking at the final asset, you can see the pieces working in unison. We combine the input from the run configuration into our prompt, which returns a result we can assume is JSON. Then we can unpack that JSON into our `UserInputSchema` schema to get further validation that our result matches what we expected.

Prompt engineering also gives us the benefit of providing the context so the user no longer has to. Now the prompt can be shortened to something like: "I'm near the The Art Institute of Chicago and driving a Kia EV9" which will result in:

```python
latitude=41.8796 longitude=-87.6237 fuel_type='ELEC'
```

## Next steps

- Continue this example with [custom resource](/examples/prompt-engineering/custom-resource)

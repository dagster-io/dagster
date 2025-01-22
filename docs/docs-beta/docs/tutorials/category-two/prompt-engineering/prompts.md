---
title: Prompts
description: Generating the first prompt
last_update:
  author: Dennis Hume
sidebar_position: 20
---

We will be working with the API for the National Renewable Energy Laboratory ([NREL](https://www.nrel.gov/)). This API allows us to find nearby alternative fuel stations. In order to use this API we need to provide our latitude and longitude and some information about our vehicle. Using AI models like Claude, we get coordinates based on an address or more free form responses. It can also help us parse our vehicle type if we include information about our car. For example if we told it: "I'm near the The Art Institute of Chicago and driving a Kia EV9, what are my coordinates and my vehicle type?", it will provide an aswer:

> Your coordinates will depend on your exact location near The Art Institute of Chicago, but its approximate coordinates are 41.8796° N, 87.6237° W. If you're nearby, your latitude and longitude should be close to these.
> 
> Your vehicle type is a Kia EV9, which is a fully electric SUV. Let me know if you need parking suggestions or other assistance nearby!

This is helpful but has a couple of issues. First it requires the user to know and include the information we will need on the backend, "...what are my coordinates and my vehicle type?". We don't want to count on the user to include that information. Also the reponse we get back will be hard to parse and we cannot guarantee that it will always be in the same format.

To get around this we can imploy prompt engineering. Prompt engineering is the process of crafting effective prompts to guide AI models toward generating accurate, relevant, or desired outputs. When including the output of AI models in data pipelines, one of the most important things is to ensure the output is in a format we expect and can work with. In this case we know the information we want back from the AI model and it would be helpful to have it in a format that is easier to parse, like JSON. We can write a prompt that both tells the models what we are interested in, the format we expect back, and give an example. In our case a prompt might look like this:

<CodeExample path="project_prompt_eng/project_prompt_eng/assets.py" language="python" lineStart="8" lineEnd="31"/>

Now we can use this prompt with Claude, all within a Dagster asset. Our asset will use the `AnthropicResource` so we can easily interact with the Anthropic client. Also because we want our pipeline to be flexible and answer different questions, we will include a run configuration so we can execute different questions at execution time.  

<CodeExample path="project_prompt_eng/project_prompt_eng/assets.py" language="python" lineStart="65" lineEnd="93"/>

Because we can ensure our model response will be a json object, we can use `json.loads` on the message which will be much easier to pass to our next asset. Now a user can ask a question without including the context and still get the answer in a format we expect. So it can be shortened to "I'm near the The Art Institute of Chicago and driving a Kia EV9" and the result will be:

```json
{
  "latitude": 41.8796,
  "longitude": -87.6237,
  "vehicle_type": "ELEC",
}
```

## Next steps

- Continue this tutorial with [custom resource](custom-resource)
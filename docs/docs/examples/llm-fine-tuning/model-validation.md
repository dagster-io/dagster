---
title: Model validation
description: Validate Fine-Tuned Model
last_update:
  author: Dennis Hume
sidebar_position: 60
---

We are going to use another asset check and tie this to our `fine_tuned_model` asset. This will be slightly more sophisticated than our file validation asset check, since it will need to use both the OpenAI resource and the output of the `enriched_graphic_novels` asset.

What we will do is take another sample of data (100 records) from our `enriched_graphic_novels`. Even though our asset check is for the `fine_tuned_model` model, we can still use the `enriched_graphic_novels` asset by including it as an `additional_ins`. Now that we have another sample of data, we can use OpenAI to try and determine the category. We will run the same sample record against the base model (`gpt-4o-mini-2024-07-18`) and our fine-tuned model (`ft:gpt-4o-mini-2024-07-18:test:goodreads:AoAYW0x3`). We can then compare the number of correct answers for both models:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" startAfter="start_model_validation" endBefore="end_model_validation"/>

We will store the accuracy of both models as metadata in the check. Because this is an asset check, this will automatically every time we run our fine-tuning asset. When we execute the pipeline, you will see our check has passed since our fine-tuned model correctly identified 76 of the genres in our sample compared to the base model which was only correct in 44 instances.

![2048 resolution](/images/examples/llm-fine-tuning/model_accuracy_1.png)

We can also execute this asset check separately from the fine-tuning job if we ever want to compare the accuracy. Running it a few more times, we can see that the accuracy is plotted:

![2048 resolution](/images/examples/llm-fine-tuning/model_accuracy_2.png)

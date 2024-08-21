---
title: '[TOPIC] example reference'
description: ''
---

# [TOPIC] examples

This reference contains a variety of examples using Dagster [TOPIC]. Each example contains:

- A summary
- Additional notes
- Links to relevant documentation
- A list of the APIs used in the example

---

## [Title of example]

[This example demonstrates [description of what the example accomplishes]

```python title="my_schedule.py"
@schedule(job=my_job, cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a schedule!")
    return SkipReason("Nothing to do")
```

|                      |     |
| -------------------- | --- |
| Notes                |     |
| Related docs         |     |
| APIs in this example |     |

---

import InspirationList from '../partials/\_InspirationList.md';

<InspirationList />

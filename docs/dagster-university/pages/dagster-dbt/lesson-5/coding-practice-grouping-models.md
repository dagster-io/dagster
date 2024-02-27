---
title: 'Practice: Grouping dbt models by layer'
module: 'dagster_essentials'
lesson: '5'
---

# Practice: Grouping dbt models by layer

Override the `get_group_name` method in your `CustomizedDagsterDbtTranslator` to group each dbt model by their layer (`marts` and `staging`).

**Hint:** `dbt_resource_props`

---

## Check your work

The method you built should look similar to the following code. Click **View answer** to view it.

**If there are differences**, compare what you wrote to the code below and change them, as this method will be used as-is in future lessons.

```python {% obfuscated="true" %}
@classmethod
def get_group_name(cls, dbt_resource_props):
    return dbt_resource_props["fqn"][1]
```
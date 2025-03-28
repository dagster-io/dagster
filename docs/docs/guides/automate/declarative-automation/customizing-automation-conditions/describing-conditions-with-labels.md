---
title: 'Describing conditions with labels'
sidebar_position: 300
---

When there are a large number of sub-conditions that make up an <PyObject section="assets" module="dagster" object="AutomationCondition" />, it can be difficult to understand and troubleshoot the condition. To make conditions easier to understand, you can attach labels to sub-conditions, which will then be displayed in the Dagster UI.

Arbitrary string labels can be attached to any node in the <PyObject section="assets" module="dagster" object="AutomationCondition" /> tree by using the `with_label()` method, allowing you to describe the purpose of a specific sub-condition. For example:

```python
from dagster import AutomationCondition

in_progress_or_failed_deps = AutomationCondition.any_deps_match(
    AutomationCondition.in_progress() | AutomationCondition.failed()
).with_label("Any deps in progress or failed")
```

Then, when viewing evaluation results in the UI, the label will display next to the condition:

![Any dependencies in progress or failed condition label in the Dagster UI](/images/guides/automate/declarative-automation/condition-label.png) -->

Hovering over or expanding the label will display its sub-conditions:

![Expanded Any dependencies in progress or failed condition label with a list of sub-conditions in the Dagster UI](/images/guides/automate/declarative-automation/condition-label-expanded.png) -->

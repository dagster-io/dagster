---
title: "Modify external code"
description: "With Dagster Pipes, you can incorporate existing code into Dagster without huge refactors. This guide shows you how to modify existing code to work with Dagster Pipes."
sidebar_position: 200
---

:::note

This is part two of the [Using Dagster Pipes to run a local subprocess](index.md) tutorial.

:::

At this point, you should have two files:

- `external_code.py` which is a standalone Python script that you want to orchestrate with Dagster.
- `dagster_code.py` which includes a Dagster asset and other Dagster definitions.

In this section, you'll learn how to modify the standalone Python script to work with [Dagster Pipes](/guides/build/external-pipelines/) in order to stream information back to Dagster. To do this, you'll:

- [Make Dagster context available in external code](#step-1-make-dagster-context-available-in-external-code)
- [Stream log messages back to Dagster](#step-2-send-log-messages-to-dagster)
- [Stream structured metadata back to Dagster](#step-3-send-structured-metadata-to-dagster)

## Step 1: Make Dagster context available in external code

Getting external code to send information back to Dagster via Dagster Pipes requires adding a few lines of code:

- Imports from `dagster-pipes`

- A call that connects to Dagster Pipes: <PyObject section="libraries" module="dagster_pipes" object="open_dagster_pipes"/> initializes the Dagster Pipes context that can be used to stream information back to Dagster. We recommend calling this function near the entry point of a pipes session.

  The `with open_dagster_pipes()` is a context manager in Python, ensuring resource setup and cleanup for a specific segment of code. It's useful for tasks requiring initial setup and final teardown, like opening and closing connections. In this case, the context manager is used to initialize and close the Dagster Pipes connection.

- An instance of the Dagster Pipes context via <PyObject section="libraries" module="dagster_pipes" object="PipesContext.get" />. You can access information like `partition_key` and `asset_key` via this context object. Refer to the [the API documentation](/api/python-api/libraries/dagster-pipes#dagster_pipes.PipesContext) for more information.

In our sample Python script, the changes would look like the following:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess/part_2/step_1/external_code.py lines=2-
import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    context = PipesContext.get()
    print(f"processing total {total_orders} orders")


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
```

## Step 2: Send log messages to Dagster

Dagster Pipes context offers a built-in logging capability that enables you to stream log messages back to Dagster. Instead of printing to the standard output, you can use the `context.log` method on <PyObject section="libraries" module="dagster_pipes" object="PipesContext" /> to send log messages back to Dagster. In this case, we’re sending an `info` level log message:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess/part_2/step_2/external_code.py
import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    context = PipesContext.get()
    context.log.info(f"processing total {total_orders} orders")


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
```

Then, the log messages will show up in the **Run details** page of the Dagster UI. You can filter the log levels to only view `info` level messages:

1. Click the **Levels** filter next to the log filter field. This will present a dropdown of all log levels.
2. Select the **info** checkbox and deselect the others. This will show only the logs marked as **info** level.

![Send log messages to Dagster](/images/guides/build/external-pipelines/subprocess/part-2-step-2-log-level.png)

## Step 3: Send structured metadata to Dagster

Sometimes, you may want to log information from your external code as structured metadata shown in the Dagster UI. Dagster Pipes context also comes with the ability to log structured metadata back to Dagster.

### Report asset materialization

Similar to [reporting materialization metadata within the Dagster process](/guides/build/assets/metadata-and-tags/), you can also report asset materialization back to Dagster from the external process.

In this example, we’re passing a piece of metadata named `total_orders` to the `metadata` parameter of the <PyObject section="libraries" module="dagster_pipes" object="PipesContext" method="report_asset_materialization" />. This payload will be sent from the external process back to Dagster:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess/part_2/step_3_materialization/external_code.py
import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    context = PipesContext.get()
    # send structured metadata back to Dagster
    context.report_asset_materialization(metadata={"total_orders": total_orders})


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
```

Then, `total_orders` will show up in the UI as structured metadata:

![Report asset materialization to Dagster](/images/guides/build/external-pipelines/subprocess/part-2-step-3-report-asset-materialization.png)

This metadata will also be displayed on the **Events** tab of the **Asset Details** page in the UI:

![View materialization events in asset details page](/images/guides/build/external-pipelines/subprocess/part-2-step-3-asset-details.png)

### Report asset checks

Dagster allows you to define and execute data quality checks on assets. Refer to the [Asset Checks](/guides/test/asset-checks) documentation for more information.

If your asset has data quality checks defined, you can report to Dagster that an asset check has been performed via <PyObject section="libraries" module="dagster_pipes" object="PipesContext" method="report_asset_check" />:

<Tabs>
<TabItem value="Report from the external code">

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess//part_2/step_3_check/external_code.py
import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    context = PipesContext.get()
    # send structured metadata back to Dagster
    context.report_asset_materialization(metadata={"total_orders": total_orders})
    # report data quality check result back to Dagster
    context.report_asset_check(
        passed=orders_df[["item_id"]].notnull().all().bool(),
        check_name="no_empty_order_check",
    )


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
```

</TabItem>
<TabItem value="Define the asset in the Dagster code">

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess/part_2/step_3_check/dagster_code.py
import shutil

from dagster import (
    AssetCheckSpec,
    AssetExecutionContext,
    Definitions,
    PipesSubprocessClient,
    asset,
    file_relative_path,
)


@asset(
    check_specs=[AssetCheckSpec(name="no_empty_order_check", asset="subprocess_asset")],
)
def subprocess_asset(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
):
    cmd = [
        shutil.which("python"),
        file_relative_path(__file__, "external_code.py"),
    ]
    return pipes_subprocess_client.run(
        command=cmd, context=context
    ).get_materialize_result()


defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
```

</TabItem>
</Tabs>

When Dagster executes the code, you’ll see an asset check event with the check result in the UI:

![Report asset checks to Dagster](/images/guides/build/external-pipelines/subprocess/part-2-step-3-report-asset-check.png)
This check result will also be displayed on the **Checks** tab of the **Asset Details** page in the UI:

![View checks in asset details page](/images/guides/build/external-pipelines/subprocess/part-2-step-3-check-tab.png)

## Finished code

At this point, your two files should look like the following:

<Tabs>
<TabItem value="External code in external_code.py">

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess/part_2/step_3_check/external_code.py
import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    context = PipesContext.get()
    # send structured metadata back to Dagster
    context.report_asset_materialization(metadata={"total_orders": total_orders})
    # report data quality check result back to Dagster
    context.report_asset_check(
        passed=orders_df[["item_id"]].notnull().all().bool(),
        check_name="no_empty_order_check",
    )


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
```

</TabItem>
<TabItem value="Dagster code in dagster_code.py">

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/subprocess/part_2/step_3_check/dagster_code.py
import shutil

from dagster import (
    AssetCheckSpec,
    AssetExecutionContext,
    Definitions,
    PipesSubprocessClient,
    asset,
    file_relative_path,
)


@asset(
    check_specs=[AssetCheckSpec(name="no_empty_order_check", asset="subprocess_asset")],
)
def subprocess_asset(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
):
    cmd = [
        shutil.which("python"),
        file_relative_path(__file__, "external_code.py"),
    ]
    return pipes_subprocess_client.run(
        command=cmd, context=context
    ).get_materialize_result()


defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
```

</TabItem>
</Tabs>

## What's next?

In this tutorial, you learned how to get access to Dagster Pipes context, report log messages events from the external process, and send structured events back to Dagster.

What's next? From here, you can:

- Learn about other capabilities of executing external code in subprocess via Dagster Pipes in the [Subprocess reference](reference)
- Learn how to [customize your own Dagster Pipes protocols](/guides/build/external-pipelines/dagster-pipes-details-and-customization)
- Learn about [other integrations with Dagster Pipes](/guides/build/external-pipelines/)

import time

import dagster as dg


# highlight-start
class ExpensiveResource(dg.ConfigurableResource):
    def addition(self, num1: int, num2: int) -> int:
        time.sleep(5)
        return num1 + num2


# highlight-end


@dg.asset
def expensive_asset(
    expensive_resource: ExpensiveResource,
) -> dg.MaterializeResult:
    value = expensive_resource.addition(1, 2)
    value = expensive_resource.addition(1, 2)
    value = expensive_resource.addition(1, 2)
    return dg.MaterializeResult(metadata={"addition": value})


@dg.asset(
    deps=[expensive_asset],
)
def another_expensive_asset(
    expensive_resource: ExpensiveResource,
) -> dg.MaterializeResult:
    value = expensive_resource.addition(1, 2)
    value = expensive_resource.addition(1, 2)
    value = expensive_resource.addition(1, 2)
    return dg.MaterializeResult(metadata={"addition": value})

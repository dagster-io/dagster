import time

# highlight-start
from functools import lru_cache

# highlight-end
import dagster as dg


# highlight-start
class ExpensiveResourceCache(dg.ConfigurableResource):
    @lru_cache(maxsize=128)
    def addition(self, num1: int, num2: int) -> int:
        time.sleep(5)
        return num1 + num2


# highlight-end


@dg.asset
def expensive_asset_cache(
    expensive_resource_cache: ExpensiveResourceCache,
) -> dg.MaterializeResult:
    value = expensive_resource_cache.addition(1, 2)
    value = expensive_resource_cache.addition(1, 2)
    value = expensive_resource_cache.addition(1, 2)
    return dg.MaterializeResult(metadata={"addition": value})


@dg.asset(
    deps=[expensive_asset_cache],
)
def another_expensive_asset_cache(
    expensive_resource_cache: ExpensiveResourceCache,
) -> dg.MaterializeResult:
    value = expensive_resource_cache.addition(1, 2)
    value = expensive_resource_cache.addition(1, 2)
    value = expensive_resource_cache.addition(1, 2)
    return dg.MaterializeResult(metadata={"addition": value})

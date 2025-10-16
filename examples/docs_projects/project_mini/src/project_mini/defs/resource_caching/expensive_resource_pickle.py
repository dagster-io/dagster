# highlight-start
import pickle

# highlight-end
import time

import dagster as dg


# highlight-start
class ExpensiveResourcePickle(dg.ConfigurableResource):
    @property
    def cache_file(self):
        return "dagster_resource_cache.pkl"

    def _load_cache(self) -> dict:
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "rb") as f:
                    return pickle.load(f)
            else:
                return {}
        except Exception:
            return {}

    def _save_cache(self, cache: dict):
        try:
            with open(self.cache_file, "wb") as f:
                pickle.dump(cache, f)
        except Exception:
            pass

    def addition(self, num1: int, num2: int) -> int:
        cache_key = (num1, num2)
        cache = self._load_cache()

        if cache_key in cache:
            return cache[cache_key]

        time.sleep(5)
        result = num1 + num2

        cache[cache_key] = result
        self._save_cache(cache)

        return result


# highlight-end


@dg.asset
def expensive_asset_pickle(
    expensive_resource_pickle: ExpensiveResourcePickle,
) -> dg.MaterializeResult:
    value = expensive_resource_pickle.addition(1, 2)
    value = expensive_resource_pickle.addition(1, 2)
    value = expensive_resource_pickle.addition(1, 2)
    return dg.MaterializeResult(metadata={"addition": value})


@dg.asset(
    deps=[expensive_asset_pickle],
)
def another_expensive_asset_pickle(
    expensive_resource_pickle: ExpensiveResourcePickle,
) -> dg.MaterializeResult:
    value = expensive_resource_pickle.addition(1, 2)
    value = expensive_resource_pickle.addition(1, 2)
    value = expensive_resource_pickle.addition(1, 2)
    return dg.MaterializeResult(metadata={"addition": value})

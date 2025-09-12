import random
import time

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetsDefinition,
    OpExecutionContext,
    asset,
    job,
    op,
)

N_ASSETS = 1000


def generate_big_honkin_assets() -> list[AssetsDefinition]:
    random.seed(5438790)
    assets = []

    for i in range(N_ASSETS):
        non_argument_deps = [
            AssetKey(f"asset_{j}") for j in random.sample(range(i), min(i, random.randint(0, 3)))
        ]

        @asset(
            name=f"asset_{i}",
            deps=non_argument_deps,
            tags={
                "test": "hi",
                "a-super-super-duper-super-longkey": "A-SUPER-DUPER-DUPER-DUPER-DUPER-LONG-VALUE",
            },
        )
        def some_asset():
            # Sleep for 10 seconds to make the asset materialization take a long time
            time.sleep(10)
            pass

        assets.append(some_asset)

    return assets


assets = generate_big_honkin_assets()


letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


@op
def create_non_sda_asset(context: OpExecutionContext):
    for i in range(100000):
        context.log_event(
            AssetMaterialization(asset_key=f"{letters[i % len(letters)]}_external_asset_{i}")
        )


@job
def big_honkin_assets_job():
    create_non_sda_asset()

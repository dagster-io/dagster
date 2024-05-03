import asyncio
from typing import List

from dagster._model import DagsterModel
from dagster._utils.aiodataloader import DataLoader


class Thing(DagsterModel):
    key: str


class ThingLoader(DataLoader[str, Thing]):
    async def batch_load_fn(self, keys: List[str]):
        print(f"Imagine: SELECT * from THINGS where keys in {keys}") # noqa: T201
        return [Thing(key=key + "_value") for key in keys]


async def two_round_trips(loader: ThingLoader, key: str):
    thing_one = await loader.load(key)
    return await loader.load(thing_one.key)


async def main() -> None:
    loader = ThingLoader()
    value1, value2 = await asyncio.gather(
        two_round_trips(loader, "key"), two_round_trips(loader, "another_key")
    )

    print(f"Value 1: {value1}. Value 2: {value2}") # noqa: T201


asyncio.run(main())

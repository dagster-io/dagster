### EXTERNAL PROCESS

import json
from collections.abc import Iterator
from contextlib import contextmanager

import cloud_service  # type: ignore
from dagster_pipes import PipesContextData, PipesContextLoader, PipesParams


class MyCustomCloudServiceContextLoader(PipesContextLoader):
    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        # params were yielded by the above context injector and sourced from the bootstrap payload
        key = params["key"]
        data = cloud_service.read(key)
        yield json.loads(data)

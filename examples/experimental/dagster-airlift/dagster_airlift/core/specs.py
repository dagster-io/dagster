from typing import Callable, List, Sequence, Union

from dagster import (
    AssetCheckSpec,
    AssetSpec,
    _check as check,
)


class Specs:
    def __init__(self, specs: Sequence[Union[AssetSpec, AssetCheckSpec]]):
        self.specs = list(
            check.opt_sequence_param(specs, "specs", of_type=(AssetSpec, AssetCheckSpec)) or []
        )

    def replace(self, **kwargs) -> "Specs":
        self.specs = [spec._replace(**kwargs) for spec in self.specs]
        return self

    def with_tags(self, tags: dict) -> "Specs":
        self.specs = [
            spec._replace(tags={**spec.tags, **tags}) if isinstance(spec, AssetSpec) else spec
            for spec in self.specs
        ]
        return self

    def with_metadata(self, metadata: dict) -> "Specs":
        self.specs = [
            spec._replace(metadata={**(spec.metadata or {}), **metadata}) for spec in self.specs
        ]
        return self

    def apply(
        self, f: Callable[[Union[AssetSpec, AssetCheckSpec]], Union[AssetSpec, AssetCheckSpec]]
    ) -> "Specs":
        self.specs = [f(spec) for spec in self.specs]
        return self

    def to_spec_list(self) -> List[Union[AssetSpec, AssetCheckSpec]]:
        return self.specs

    def to_asset_spec_list(self) -> List[AssetSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetSpec)]

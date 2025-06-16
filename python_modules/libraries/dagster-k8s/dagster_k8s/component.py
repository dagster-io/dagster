from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Optional, Union

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    Component,
    ComponentLoadContext,
    Definitions,
    Resolvable,
    ResolvedAssetSpec,
    multi_asset,
)

from dagster_k8s.pipes import PipesK8sClient, build_pod_body


@dataclass
class PipesK8sComponent(Component, Resolvable):
    """Component that creates assets backed by kubernetes pod execution via Dagster Pipes."""

    name: str
    assets: Sequence[ResolvedAssetSpec]
    image: Optional[str] = None
    command: Optional[Union[str, Sequence[str]]] = None
    namespace: Optional[str] = None
    env: Optional[Mapping[str, str]] = None
    base_pod_meta: Optional[Mapping[str, Any]] = None
    base_pod_spec: Optional[Mapping[str, Any]] = None

    def __post_init__(self):
        # validate that we can build a pod for the given args
        # i.e. image or base_pod_self.image
        build_pod_body(
            pod_name=self.name,
            image=self.image,
            command=self.command,
            env_vars=self.env or {},
            base_pod_meta=self.base_pod_meta,
            base_pod_spec=self.base_pod_spec,
        )

    @cached_property
    def client(self):
        return PipesK8sClient()

    def build_defs(self, context: ComponentLoadContext):
        return Definitions(assets=[self.build_asset()])

    def build_asset(self) -> AssetsDefinition:
        @multi_asset(name=self.name, specs=self.assets)
        def _asset(context: AssetExecutionContext):
            return self.client.run(
                context=context,
                image=self.image,
                command=self.command,
                namespace=self.namespace,
                env=self.env,
                base_pod_meta=self.base_pod_meta,
                base_pod_spec=self.base_pod_spec,
            ).get_results()

        return _asset

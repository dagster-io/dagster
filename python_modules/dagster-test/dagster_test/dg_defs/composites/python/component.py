from dagster import (
    AssetSpec,
    Component,
    Definitions,
    Model,
    Resolvable,
    ResolvedAssetSpec,
    component_instance,
)


class PyComponent(Component, Model, Resolvable):
    asset: ResolvedAssetSpec

    def build_defs(self, context):
        return Definitions(assets=[self.asset])


@component_instance
def first(_):
    return PyComponent(asset=AssetSpec("first_py"))


@component_instance
def second(_):
    return PyComponent(asset=AssetSpec("second_py"))

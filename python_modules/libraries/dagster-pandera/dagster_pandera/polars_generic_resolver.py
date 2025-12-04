from __future__ import annotations

import typing as t

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType
from dagster._core.types.generic_resolver import register_generic_type_resolver

try:
    import pandera as pa
    import pandera.typing.polars as pa_pl
    import polars as pl
except ImportError:  # pragma: no cover
    pa = None
    pa_pl = None
    pl = None

# ``pandera_schema_to_dagster_type`` lives in the dagster-pandera integration.
try:  # pragma: no cover
    from dagster_pandera import pandera_schema_to_dagster_type
except ImportError:  # pragma: no cover
    pandera_schema_to_dagster_type = None


def _build_polars_resolver(*, is_lazy: bool) -> t.Callable[[t.Tuple[object, ...]], DagsterType]:
    runtime_type = pl.LazyFrame if is_lazy else pl.DataFrame

    def _resolver(type_args: t.Tuple[object, ...]) -> DagsterType:
        if pandera_schema_to_dagster_type is None or pa is None or pa_pl is None or pl is None:
            raise DagsterInvalidDefinitionError(
                "Pandera + Polars generic support requires pandera, polars, and dagster-pandera."
            )

        if len(type_args) != 1:
            raise DagsterInvalidDefinitionError(
                "Pandera Polars generics expect a single schema type argument."
            )

        schema_cls = type_args[0]
        if not isinstance(schema_cls, type) or not issubclass(schema_cls, pa.DataFrameModel):
            raise DagsterInvalidDefinitionError(
                "Pandera Polars generics must be parametrized with a pandera.DataFrameModel subclass."
            )

        base_type = pandera_schema_to_dagster_type(schema_cls)

        def _type_check(context, value):
            materialized_value = value
            if is_lazy and hasattr(materialized_value, "collect"):
                materialized_value = materialized_value.collect()
            return base_type.type_check(context, materialized_value)

        generic_label = "LazyFrame" if is_lazy else "DataFrame"
        key = f"PanderaPolars[{schema_cls.__module__}.{schema_cls.__name__}:{generic_label}]"

        # Wrap the Pandera DagsterType so we can control typing_type for IOManagers/tooling.
        return DagsterType(
            type_check_fn=_type_check,
            key=key,
            description=base_type.description,
            loader=base_type.loader,
            required_resource_keys=set(base_type.required_resource_keys),
            kind=base_type.kind,
            typing_type=runtime_type,
            metadata=base_type.metadata,
        )

    return _resolver


def register_pandera_polars_generic_resolvers() -> None:
    """Example hook showing how to register Pandera + Polars generics."""

    if pa_pl is None or pandera_schema_to_dagster_type is None:
        raise ImportError(
            "pandera.typing.polars and dagster-pandera must be installed to register generics"
        )

    register_generic_type_resolver(pa_pl.DataFrame, _build_polars_resolver(is_lazy=False))
    register_generic_type_resolver(pa_pl.LazyFrame, _build_polars_resolver(is_lazy=True))

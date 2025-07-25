from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Generic, Optional, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import (
    AssetAttributesModel,
    resolve_asset_spec_update_kwargs_to_mapping,
)
from dagster.components.resolved.model import Resolver

TRANSLATOR_MERGE_ATTRIBUTES = {"metadata", "tags"}


@dataclass
class TranslatorResolvingInfo:
    asset_attributes: Union[str, BaseModel]
    resolution_context: ResolutionContext
    model_key: str = "asset_attributes"

    def _resolve_asset_attributes(self, context: Mapping[str, Any]) -> Union[AssetSpec, BaseModel]:
        """Resolves the user-specified asset attributes into an AssetAttributesModel, or an AssetSpec
        if the UDF returns one.
        """
        if not isinstance(self.asset_attributes, str):
            return self.asset_attributes

        resolved_asset_attributes = (
            self.resolution_context.at_path(self.model_key)
            .with_scope(**context)
            .resolve_value(self.asset_attributes)
        )

        if isinstance(resolved_asset_attributes, AssetSpec):
            return resolved_asset_attributes
        elif isinstance(resolved_asset_attributes, AssetAttributesModel):
            return resolved_asset_attributes
        elif isinstance(resolved_asset_attributes, dict):
            return AssetAttributesModel(**(resolved_asset_attributes))
        else:
            check.failed(
                f"Unexpected return value for asset_attributes UDF: {type(resolved_asset_attributes)}"
            )

    def get_asset_spec(self, base_spec: AssetSpec, context: Mapping[str, Any]) -> AssetSpec:
        """Returns an AssetSpec that combines the base spec with attributes resolved using the provided context.

        Usage:

        ```python
        class WrappedDagsterXTranslator(DagsterXTranslator):
            def __init__(self, *, base_translator, resolving_info: TranslatorResolvingInfo):
                self.base_translator = base_translator
                self.resolving_info = resolving_info

            def get_asset_spec(self, base_spec: AssetSpec, x_params: Any) -> AssetSpec:
                return self.resolving_info.get_asset_spec(
                    base_spec, {"x_params": x_params}
                )

        ```
        """
        resolved_asset_attributes = self._resolve_asset_attributes(context)
        if isinstance(resolved_asset_attributes, AssetSpec):
            return resolved_asset_attributes

        resolved_attributes = dict(
            resolve_asset_spec_update_kwargs_to_mapping(
                model=resolved_asset_attributes,
                context=self.resolution_context.at_path(self.model_key).with_scope(**context),
            )
        )
        if "code_version" in resolved_attributes:
            resolved_attributes = {
                **resolved_attributes,
                "code_version": str(resolved_attributes["code_version"]),
            }

        if "key_prefix" in resolved_attributes:
            prefix = resolved_attributes.pop("key_prefix")
            if "key" in resolved_attributes:
                key = resolved_attributes.pop("key")
            else:
                key = base_spec.key
            key = key.with_prefix(prefix)
            resolved_attributes["key"] = key

        return base_spec.replace_attributes(
            **{k: v for k, v in resolved_attributes.items() if k not in TRANSLATOR_MERGE_ATTRIBUTES}
        ).merge_attributes(
            **{k: v for k, v in resolved_attributes.items() if k in TRANSLATOR_MERGE_ATTRIBUTES}
        )


T = TypeVar("T")

TranslationFn: TypeAlias = Callable[[AssetSpec, T], AssetSpec]


class TranslatorResolvable(Resolvable, Generic[T]):
    translation: Any = None  # Will be properly set up by __init_subclass__

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Each subclass gets its own resolver that calls the correct class methods
        # We need to capture the class in a closure to avoid late binding issues
        def make_resolver_func(target_cls):
            return lambda context, model: target_cls.resolve_translation(context, model)

        cls.__annotations__["translation"] = Optional[
            Annotated[
                TranslationFn[T],
                Resolver(
                    make_resolver_func(cls),
                    inject_before_resolve=False,
                    model_field_type=Union[str, AssetAttributesModel],
                ),
            ]
        ]

        # if cls.get_translator_field_description():
        #     cls.__annotations__["translation"] = Field(
        #         cls.__annotations__["translation"],
        #         description=cls.get_translator_field_description(),
        #     )

    @classmethod
    def get_template_vars_for_translation(cls, data: T) -> Mapping[str, Any]:
        return {"data": data}

    @classmethod
    def get_translator_field_description(cls) -> Optional[str]:
        return None

    @classmethod
    def resolve_translation(cls, context: ResolutionContext, model) -> TranslationFn[T]:
        template_vars = cls.get_template_vars_for_translation(model)
        info = TranslatorResolvingInfo(
            asset_attributes=model,
            resolution_context=context,
            model_key="translation",
        )
        return lambda base_asset_spec, data: info.get_asset_spec(
            base_asset_spec,
            {
                **template_vars,
                "spec": base_asset_spec,
            },
        )

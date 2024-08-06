from dataclasses import dataclass
from typing import Optional

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._annotations import public

from .asset_utils import default_asset_key_fn


@dataclass(frozen=True)
class DagsterSdfTranslatorSettings:
    """Settings to enable Dagster features for your sdf project."""


class DagsterSdfTranslator:
    """Holds a set of methods that derive Dagster asset definition metadata given a representation
    of an sdf resource (models, tests, sources, etc).

    This class is exposed so that methods can be overriden to customize how Dagster asset metadata
    is derived.
    """

    def __init__(self, settings: Optional[DagsterSdfTranslatorSettings] = None):
        """Initialize the translator.

        Args:
            settings (Optional[DagsterSdfTranslatorSettings]): Settings for the translator.
        """
        self._settings = settings or DagsterSdfTranslatorSettings()

    @property
    def settings(self) -> DagsterSdfTranslatorSettings:
        if not hasattr(self, "_settings"):
            self._settings = DagsterSdfTranslatorSettings()

        return self._settings

    @public
    def get_asset_key(self, fqn: str) -> AssetKey:
        return default_asset_key_fn(fqn)


def validate_translator(dagster_sdf_translator: DagsterSdfTranslator) -> DagsterSdfTranslator:
    return check.inst_param(
        dagster_sdf_translator,
        "dagster_sdf_translator",
        DagsterSdfTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterSdfTranslator."
        ),
    )


def validate_opt_translator(
    dagster_sdf_translator: Optional[DagsterSdfTranslator],
) -> Optional[DagsterSdfTranslator]:
    return check.opt_inst_param(
        dagster_sdf_translator,
        "dagster_sdf_translator",
        DagsterSdfTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterSdfTranslator."
        ),
    )

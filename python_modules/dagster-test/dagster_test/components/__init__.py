import importlib.util

_has_dagster_components = importlib.util.find_spec("dagster_components") is not None

if not _has_dagster_components:
    raise Exception("dagster-components is not installed")

from dagster_test.components.all_metadata_empty_asset import (
    AllMetadataEmptyComponent as AllMetadataEmptyComponent,
)
from dagster_test.components.complex_schema_asset import (
    ComplexAssetComponent as ComplexAssetComponent,
)
from dagster_test.components.scaffoldable_function import scaffoldable_fn as scaffoldable_fn
from dagster_test.components.simple_asset import SimpleAssetComponent as SimpleAssetComponent
from dagster_test.components.simple_pipes_script_asset import (
    SimplePipesScriptComponent as SimplePipesScriptComponent,
)

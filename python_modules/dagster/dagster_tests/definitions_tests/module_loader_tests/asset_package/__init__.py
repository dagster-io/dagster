from dagster import AssetKey, SourceAsset, asset
from dagster._core.definitions.asset_spec import AssetSpec


@asset
def little_richard():
    pass


def make_list_of_assets():
    # these assets are stashed inside a function so that they need to be discovered through
    # a list
    @asset
    def james_brown():
        pass

    @asset(metadata={"foo": "bar"})
    def fats_domino():
        pass

    return [james_brown, fats_domino]


def make_list_of_source_assets():
    # these source assets are stashed inside a function so that they need to be discovered through
    # a list
    buddy_holly = SourceAsset(key=AssetKey("buddy_holly"))
    jerry_lee_lewis = SourceAsset(key=AssetKey("jerry_lee_lewis"))

    return [buddy_holly, jerry_lee_lewis]


top_level_spec = AssetSpec("top_level_spec")


list_of_assets_and_source_assets = [*make_list_of_assets(), *make_list_of_source_assets()]

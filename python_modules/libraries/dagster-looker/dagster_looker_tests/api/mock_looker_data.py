from looker_sdk.sdk.api40.models import LookmlModel, LookmlModelExplore, LookmlModelNavExplore

mock_lookml_models = [
    LookmlModel(
        explores=[
            LookmlModelNavExplore(name="my_explore"),
        ],
        name="my_model",
    )
]

mock_lookml_explore = LookmlModelExplore(id="my_model::my_explore")

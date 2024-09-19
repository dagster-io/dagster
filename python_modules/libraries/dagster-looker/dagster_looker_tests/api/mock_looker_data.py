from looker_sdk.sdk.api40.models import (
    Dashboard,
    DashboardBase,
    DashboardFilter,
    LookmlModel,
    LookmlModelExplore,
    LookmlModelNavExplore,
)

mock_lookml_models = [
    LookmlModel(
        explores=[
            LookmlModelNavExplore(name="my_explore"),
        ],
        name="my_model",
    )
]

mock_lookml_explore = LookmlModelExplore(id="my_model::my_explore")

mock_looker_dashboard_bases = [
    DashboardBase(id="1", hidden=False),
    DashboardBase(id="2", hidden=True),
]

mock_looker_dashboard = Dashboard(
    title="my_dashboard",
    id="1",
    dashboard_filters=[
        DashboardFilter(model="my_model", explore="my_explore"),
    ],
)

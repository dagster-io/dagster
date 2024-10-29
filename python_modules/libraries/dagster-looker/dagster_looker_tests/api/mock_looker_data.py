import json

from looker_sdk.sdk.api40.models import (
    Dashboard,
    DashboardBase,
    DashboardFilter,
    LookmlModel,
    LookmlModelExplore,
    LookmlModelNavExplore,
    MaterializePDT,
    User,
)

mock_lookml_models = [
    LookmlModel(
        explores=[
            LookmlModelNavExplore(name="my_explore"),
        ],
        name="my_model",
    )
]

mock_lookml_explore = LookmlModelExplore(
    id="my_model::my_explore", view_name="my_view", sql_table_name="my_table"
)

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
    user_id="1",
    url="/dashboards/1",
)

mock_other_looker_dashboard = Dashboard(
    title="my_dashboard_2",
    id="2",
    dashboard_filters=[
        DashboardFilter(model="my_model", explore="my_other_explore"),
    ],
    user_id="2",
    url="/dashboards/2",
)

mock_user = User(id="1", email="ben@dagsterlabs.com")

mock_other_user = User(
    id="2",
    email="rex@dagsterlabs.com",
)

mock_start_pdt_build = MaterializePDT(
    materialization_id="100",
)
mock_check_pdt_build = MaterializePDT(
    materialization_id="100",
    resp_text=json.dumps({"status": "running"}),
)

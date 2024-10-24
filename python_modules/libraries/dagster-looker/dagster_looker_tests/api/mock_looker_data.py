import json

from looker_sdk.sdk.api40.models import (
    Dashboard,
    DashboardBase,
    DashboardFilter,
    FolderBase,
    LookmlModel,
    LookmlModelExplore,
    LookmlModelNavExplore,
    MaterializePDT,
)

mock_lookml_models = [
    LookmlModel(
        explores=[
            LookmlModelNavExplore(name="my_explore"),
            LookmlModelNavExplore(name="my_other_explore"),
        ],
        name="my_model",
    )
]

mock_lookml_explore = LookmlModelExplore(
    id="my_model::my_explore", view_name="my_view", sql_table_name="my_table"
)
mock_lookml_other_explore = LookmlModelExplore(
    id="my_model::my_other_explore", view_name="my_view", sql_table_name="my_table"
)

mock_folders = [
    FolderBase(parent_id=None, name="my_folder", id="1"),
    FolderBase(parent_id="1", name="my_subfolder", id="2"),
    FolderBase(parent_id="1", name="my_other_subfolder", id="3"),
]

mock_looker_dashboard_bases = [
    DashboardBase(
        id="1", hidden=False, folder=FolderBase(name="my_subfolder", id="2", parent_id="1")
    ),
    DashboardBase(
        id="2", hidden=False, folder=FolderBase(name="my_other_subfolder", id="3", parent_id="1")
    ),
    DashboardBase(id="3", hidden=True),
]

mock_looker_dashboard = Dashboard(
    title="my_dashboard",
    id="1",
    dashboard_filters=[
        DashboardFilter(model="my_model", explore="my_explore"),
    ],
)

mock_other_looker_dashboard = Dashboard(
    title="my_dashboard_2",
    id="2",
    dashboard_filters=[
        DashboardFilter(model="my_model", explore="my_other_explore"),
    ],
)

mock_start_pdt_build = MaterializePDT(
    materialization_id="100",
)
mock_check_pdt_build = MaterializePDT(
    materialization_id="100",
    resp_text=json.dumps({"status": "running"}),
)

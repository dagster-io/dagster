from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._seven import json
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
)


async def handle_report_asset_materialization_request(
    context: BaseWorkspaceRequestContext,
    request: Request,
) -> JSONResponse:
    # Record a runless asset materialization event.
    # The asset key is passed as url path with / delimiting parts or as a query param.
    # Properties can be passed as json post body or query params, with that order of precedence.

    body_content_type = request.headers.get("content-type")
    if body_content_type is None:
        json_body = {}
    elif body_content_type == "application/json":
        json_body = await request.json()
    else:
        return JSONResponse(
            {
                "error": (
                    f"Unhandled content type {body_content_type}, expect no body or"
                    " application/json"
                ),
            },
            status_code=400,
        )

    asset_key = None
    if request.path_params.get(ReportAssetMatParam.asset_key):
        # use from_user_string to treat / as multipart key separator
        asset_key = AssetKey.from_user_string(request.path_params["asset_key"])
    elif ReportAssetMatParam.asset_key in json_body:
        asset_key = AssetKey(json_body[ReportAssetMatParam.asset_key])
    elif ReportAssetMatParam.asset_key in request.query_params:
        asset_key = AssetKey.from_db_string(request.query_params["asset_key"])

    if asset_key is None:
        return JSONResponse(
            {
                "error": (
                    "Empty asset key, must provide asset key as url path after"
                    " /report_asset_materialization/ or query param asset_key."
                ),
            },
            status_code=400,
        )

    tags = None
    if ReportAssetMatParam.data_version in json_body:
        tags = {
            DATA_VERSION_TAG: json_body[ReportAssetMatParam.data_version],
            DATA_VERSION_IS_USER_PROVIDED_TAG: "true",
        }
    elif ReportAssetMatParam.data_version in request.query_params:
        tags = {
            DATA_VERSION_TAG: request.query_params[ReportAssetMatParam.data_version],
            DATA_VERSION_IS_USER_PROVIDED_TAG: "true",
        }

    partition = None
    if ReportAssetMatParam.partition in json_body:
        partition = json_body[ReportAssetMatParam.partition]
    elif ReportAssetMatParam.partition in request.query_params:
        partition = request.query_params[ReportAssetMatParam.partition]

    description = None
    if ReportAssetMatParam.description in json_body:
        description = json_body[ReportAssetMatParam.description]
    elif ReportAssetMatParam.description in request.query_params:
        description = request.query_params[ReportAssetMatParam.description]

    metadata = None
    if ReportAssetMatParam.metadata in json_body:
        metadata = json_body[ReportAssetMatParam.metadata]
    elif ReportAssetMatParam.metadata in request.query_params:
        try:
            metadata = json.loads(request.query_params[ReportAssetMatParam.metadata])
        except Exception as exc:
            return JSONResponse(
                {
                    "error": f"Error parsing metadata json: {exc}",
                },
                status_code=400,
            )

    try:
        mat = AssetMaterialization(
            asset_key=asset_key,
            partition=partition,
            metadata=metadata,
            description=description,
            tags=tags,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "error": f"Error constructing AssetMaterialization: {exc}",
            },
            status_code=400,
        )

    context.instance.report_runless_asset_event(mat)

    return JSONResponse({})


class ReportAssetMatParam:
    """Class to collect all supported args by report_asset_materialization endpoint
    to ensure consistency with related APIs.

    note: Enum not used to avoid value type problems X(str, Enum) doesn't work as partition conflicts with keyword
    """

    asset_key = "asset_key"
    data_version = "data_version"
    metadata = "metadata"
    description = "description"
    partition = "partition"

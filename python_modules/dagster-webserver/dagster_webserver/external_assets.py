from typing import Any

import dagster._check as check
from dagster import AssetObservation
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster_shared.seven import json
from starlette.requests import Request
from starlette.responses import JSONResponse


def _asset_key_from_request(key: str, request: Request, json_body):
    check.invariant(key == "asset_key")  #

    if request.path_params.get(key):
        # use from_user_string to treat / as multipart key separator
        return AssetKey.from_user_string(request.path_params["asset_key"])
    elif ReportAssetMatParam.asset_key in json_body:
        return AssetKey(json_body[ReportAssetMatParam.asset_key])
    elif ReportAssetMatParam.asset_key in request.query_params:
        return AssetKey.from_db_string(request.query_params["asset_key"])

    return None


def _value_from_body_or_params(key: str, request: Request, json_body) -> Any:
    if key in json_body:
        return json_body[key]
    elif key in request.query_params:
        return request.query_params[key]
    return None


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

    asset_key = _asset_key_from_request(ReportAssetMatParam.asset_key, request, json_body)
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

    tags = context.get_reporting_user_tags()
    data_version = _value_from_body_or_params(ReportAssetMatParam.data_version, request, json_body)
    if data_version is not None:
        tags[DATA_VERSION_TAG] = data_version
        tags[DATA_VERSION_IS_USER_PROVIDED_TAG] = "true"

    partition = _value_from_body_or_params(ReportAssetMatParam.partition, request, json_body)
    description = _value_from_body_or_params(ReportAssetMatParam.description, request, json_body)

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


async def handle_report_asset_check_request(
    context: BaseWorkspaceRequestContext,
    request: Request,
) -> JSONResponse:
    # Record a runless asset check evaluation event.
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

    asset_key = _asset_key_from_request(ReportAssetCheckEvalParam.asset_key, request, json_body)
    if asset_key is None:
        return JSONResponse(
            {
                "error": (
                    "Empty asset key, must provide asset key as url path after"
                    " /report_asset_check_evaluation/ or query param asset_key."
                ),
            },
            status_code=400,
        )

    passed = _value_from_body_or_params(ReportAssetCheckEvalParam.passed, request, json_body)
    check_name = _value_from_body_or_params(
        ReportAssetCheckEvalParam.check_name, request, json_body
    )
    severity = _value_from_body_or_params(ReportAssetCheckEvalParam.severity, request, json_body)
    if severity is None:
        severity = "ERROR"  # default

    if ReportAssetCheckEvalParam.passed in json_body:
        passed = json_body[ReportAssetCheckEvalParam.passed]
    elif ReportAssetCheckEvalParam.passed in request.query_params:
        try:
            passed = json.loads(request.query_params[ReportAssetCheckEvalParam.passed])
        except Exception as exc:
            return JSONResponse(
                {
                    "error": f"Error parsing 'passed': {exc}",
                },
                status_code=400,
            )
    else:
        return JSONResponse(
            {
                "error": "Missing required parameter 'passed'.",
            },
            status_code=400,
        )

    metadata = {}
    if ReportAssetCheckEvalParam.metadata in json_body:
        metadata = json_body[ReportAssetCheckEvalParam.metadata]
    elif ReportAssetCheckEvalParam.metadata in request.query_params:
        try:
            metadata = json.loads(request.query_params[ReportAssetCheckEvalParam.metadata])
        except Exception as exc:
            return JSONResponse(
                {
                    "error": f"Error parsing metadata json: {exc}",
                },
                status_code=400,
            )

    try:
        evaluation = AssetCheckEvaluation(
            check_name=check_name,
            passed=passed,
            asset_key=asset_key,
            metadata=metadata,
            severity=AssetCheckSeverity(severity),
        )
    except Exception as exc:
        return JSONResponse(
            {
                "error": f"Error constructing AssetCheckEvaluation: {exc}",
            },
            status_code=400,
        )

    context.instance.report_runless_asset_event(evaluation)

    return JSONResponse({})


async def handle_report_asset_observation_request(
    context: BaseWorkspaceRequestContext,
    request: Request,
) -> JSONResponse:
    # Record a runless asset observation event.
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

    asset_key = _asset_key_from_request(ReportAssetObsParam.asset_key, request, json_body)
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

    metadata = {}
    if ReportAssetObsParam.metadata in json_body:
        metadata = json_body[ReportAssetObsParam.metadata]
    elif ReportAssetObsParam.metadata in request.query_params:
        try:
            metadata = json.loads(request.query_params[ReportAssetObsParam.metadata])
        except Exception as exc:
            return JSONResponse(
                {
                    "error": f"Error parsing metadata json: {exc}",
                },
                status_code=400,
            )

    partition = _value_from_body_or_params(ReportAssetObsParam.partition, request, json_body)
    description = _value_from_body_or_params(ReportAssetObsParam.description, request, json_body)

    tags = context.get_reporting_user_tags()
    data_version = _value_from_body_or_params(ReportAssetObsParam.data_version, request, json_body)
    if data_version is not None:
        tags[DATA_VERSION_TAG] = data_version
        tags[DATA_VERSION_IS_USER_PROVIDED_TAG] = "true"

    try:
        observation = AssetObservation(
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

    context.instance.report_runless_asset_event(observation)

    return JSONResponse({})


# note: Enum not used to avoid value type problems X(str, Enum) doesn't work as partition conflicts with keyword
class ReportAssetMatParam:
    """Class to collect all supported args by report_asset_materialization endpoint
    to ensure consistency with related APIs.
    """

    asset_key = "asset_key"
    data_version = "data_version"
    metadata = "metadata"
    description = "description"
    partition = "partition"


class ReportAssetCheckEvalParam:
    """Class to collect all supported args by report_asset_check endpoint
    to ensure consistency with related APIs.
    """

    asset_key = "asset_key"
    check_name = "check_name"
    metadata = "metadata"
    severity = "severity"
    passed = "passed"


class ReportAssetObsParam:
    """Class to collect all supported args by report_asset_observation endpoint
    to ensure consistency with related APIs.
    """

    asset_key = "asset_key"
    data_version = "data_version"
    metadata = "metadata"
    description = "description"
    partition = "partition"

from dagster.utils.merger import deep_merge_dicts

DEFAULT_CONNECTOR_ID = "some_connector"


def get_sample_connector_response(**kwargs):
    return deep_merge_dicts(
        {
            "code": "Success",
            "data": {
                "id": DEFAULT_CONNECTOR_ID,
                "group_id": "some_group",
                "service": "some_service",
                "service_version": 1,
                "schema": "some_service.some_name",
                "connected_by": "some_user",
                "created_at": "2021-01-01T00:00:00.0Z",
                "succeeded_at": "2021-01-01T01:00:00.0Z",
                "failed_at": None,
                "paused": False,
                "pause_after_trial": False,
                "sync_frequency": 360,
                "schedule_type": "auto",
                "status": {
                    "setup_state": "connected",
                    "sync_state": "scheduled",
                    "update_state": "on_schedule",
                    "is_historical_sync": False,
                    "tasks": [],
                    "warnings": [],
                },
                "config": {
                    "auth_type": "OAuth",
                },
                "source_sync_details": {"last_synced": "2021-10-27T16:58:40.035Z"},
            },
        },
        kwargs,
    )


def get_sample_update_response():
    return {
        "code": "Success",
        "message": "Connector has been updated",
        "data": get_sample_connector_response()["data"],
    }


def get_sample_sync_response():
    return {
        "code": "Success",
        "message": "Sync has been successfully triggered for connector with id 'some_connector'",
    }

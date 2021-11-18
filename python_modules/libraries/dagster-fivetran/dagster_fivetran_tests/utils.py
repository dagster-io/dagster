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


def get_sample_connector_schema_config():

    return {
        "code": "Success",
        "data": {
            "enable_new_by_default": False,
            "schemas": {
                "schema_1": {
                    "name_in_destination": "xyz1",
                    "enabled": True,
                    "tables": {
                        "table_1": {
                            "name_in_destination": "abc1",
                            "enabled": True,
                            "enabled_patch_settings": {"allowed": True},
                            "columns": {
                                "column_1": {
                                    "name_in_destination": "column_1",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason_code": "SYSTEM_COLUMN",
                                        "reason": "The column does not support exclusion as it is a Primary Key",
                                    },
                                },
                                "column_2": {
                                    "name_in_destination": "column_2",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {"allowed": True},
                                },
                                "column_3": {
                                    "name_in_destination": "column_3",
                                    "enabled": True,
                                    "hashed": True,
                                    "enabled_patch_settings": {"allowed": True},
                                },
                            },
                        },
                        "table_2": {
                            "name_in_destination": "abc2",
                            "enabled": True,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "SYSTEM_TABLE",
                            },
                        },
                    },
                },
                "schema_2": {
                    "name_in_destination": "abc",
                    "enabled": True,
                    "tables": {
                        "table_1": {
                            "name_in_destination": "xyz",
                            "enabled": True,
                            "enabled_patch_settings": {"allowed": True},
                            "columns": {
                                "name_in_destination": "column_1",
                                "column_1": {"enabled": False},
                            },
                        },
                        "table_2": {
                            "name_in_destination": "fed",
                            "enabled": False,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "OTHER",
                                "reason": "Permission denied",
                            },
                        },
                    },
                },
                "schema_3": {
                    "name_in_destination": "qwerty",
                    "enabled": False,
                    "tables": {
                        "table_1": {
                            "name_in_destination": "bar",
                            "enabled": True,
                            "enabled_patch_settings": {"allowed": True},
                            "columns": {
                                "name_in_destination": "column_1",
                                "column_1": {"enabled": False},
                            },
                        },
                        "table_2": {
                            "name_in_destination": "fed",
                            "enabled": True,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "OTHER",
                                "reason": "Permission denied",
                            },
                        },
                    },
                },
            },
        },
    }


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

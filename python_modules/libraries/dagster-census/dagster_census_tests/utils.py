def get_sync_data():

    return {
        "status": "success",
        "data": {
            "id": 61,
            "label": None,
            "schedule_frequency": "never",
            "schedule_day": None,
            "schedule_hour": None,
            "schedule_minute": None,
            "created_at": "2021-10-22T00:40:11.246Z",
            "updated_at": "2021-10-22T00:43:44.173Z",
            "operation": "upsert",
            "paused": False,
            "status": "Ready",
            "lead_union_insert_to": None,
            "trigger_on_dbt_cloud_rebuild": False,
            "field_behavior": "specific_properties",
            "field_normalization": None,
            "source_attributes": {
                "connection_id": 15,
                "object": {
                    "type": "model",
                    "id": 15,
                    "name": "braze_test",
                    "created_at": "2021-10-11T20:52:58.293Z",
                    "updated_at": "2021-10-14T23:15:18.508Z",
                    "query": "select email, cast('random' as VARCHAR(2000)) as random_prop",
                },
            },
            "destination_attributes": {"connection_id": 15, "object": "user"},
            "mappings": [
                {
                    "from": {"type": "column", "data": "EMAIL"},
                    "to": "external_id",
                    "is_primary_identifier": True,
                    "generate_field": False,
                    "preserve_values": False,
                    "operation": None,
                },
                {
                    "from": {
                        "type": "constant_value",
                        "data": {"value": "test", "basic_type": "text"},
                    },
                    "to": "first_name",
                    "is_primary_identifier": False,
                    "generate_field": False,
                    "preserve_values": False,
                    "operation": None,
                },
            ],
        },
    }


def get_source_data():

    return {
        "status": "success",
        "data": {
            "id": 15,
            "name": "Snowflake - xxxxxxx.us-east-1",
            "label": None,
            "type": "snowflake",
            "last_test_succeeded": None,
            "last_tested_at": None,
            "connection_details": {
                "account": "xxxxxxx.us-east-1",
                "user": "DEV",
                "warehouse": "TEST",
                "use_keypair": False,
            },
            "read_only_connection": False,
        },
    }


def get_destination_data():

    return {
        "status": "success",
        "data": {
            "id": 15,
            "name": "Braze",
            "connection_details": {"instance_url": "https://rest.iad-03.braze.com"},
            "objects": [
                {
                    "label": "User",
                    "full_name": "user",
                    "allow_custom_fields": True,
                    "allow_case_sensitive_field_names": True,
                },
                {
                    "label": "Event",
                    "full_name": "event",
                    "allow_custom_fields": True,
                    "allow_case_sensitive_field_names": True,
                },
            ],
        },
    }


def get_sync_run_data():

    return {
        "status": "success",
        "data": {
            "id": 94,
            "sync_id": 52,
            "source_record_count": 1,
            "records_processed": 1,
            "records_updated": 1,
            "records_failed": 0,
            "records_invalid": 0,
            "created_at": "2021-10-20T02:51:07.546Z",
            "updated_at": "2021-10-20T02:52:29.236Z",
            "completed_at": "2021-10-20T02:52:29.234Z",
            "scheduled_execution_time": None,
            "error_code": None,
            "error_message": None,
            "error_detail": None,
            "status": "completed",
            "canceled": False,
            "full_sync": True,
            "sync_trigger_reason": {
                "ui_tag": "Manual",
                "ui_detail": "Manually triggered by test@getcensus.com",
            },
        },
    }


def get_sync_trigger_data():

    return {"status": "success", "data": {"sync_run_id": 94}}

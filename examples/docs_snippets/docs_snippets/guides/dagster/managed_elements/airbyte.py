# isort: skip_file
# pylint: disable=unused-variable


def scope_define_reconciler():
    # start_define_reconciler
    from dagster_airbyte import AirbyteManagedElementReconciler, airbyte_resource

    airbyte_instance = airbyte_resource.configured(
        {
            "host": "localhost",
            "port": "8000",
            # If using basic auth, include username and password:
            "username": "airbyte",
            "password": {"env": "AIRBYTE_PASSWORD"},
        }
    )

    airbyte_reconciler = AirbyteManagedElementReconciler(
        airbyte=airbyte_instance,
        connections=[],
    )
    # end_define_reconciler

    # start_define_sources
    from dagster_airbyte import AirbyteSource, AirbyteDestination

    cereals_csv_source = AirbyteSource(
        name="cereals-csv",
        source_type="File",
        source_configuration={
            "url": "https://docs.dagster.io/assets/cereal.csv",
            "format": "csv",
            "provider": {"storage": "HTTPS", "user_agent": False},
            "dataset_name": "cereals",
        },
    )

    local_json_destination = AirbyteDestination(
        name="local-json",
        destination_type="Local JSON",
        destination_configuration={"destination_path": "/local/cereals_out.json"},
    )
    # end_define_sources

    # start_define_connection
    from dagster_airbyte import AirbyteConnection, AirbyteSyncMode

    cereals_connection = AirbyteConnection(
        name="download-cereals",
        source=cereals_csv_source,
        destination=local_json_destination,
        stream_config={"cereals": AirbyteSyncMode.FULL_REFRESH_OVERWRITE},
    )
    # end_define_connection

    # start_new_reconciler
    airbyte_reconciler = AirbyteManagedElementReconciler(
        airbyte=airbyte_instance,
        connections=[cereals_connection],
    )
    # end_new_reconciler

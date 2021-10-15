from docs_snippets_crag.concepts.partitions_schedules_sensors.date_config_job import do_stuff


def test_do_stuff():
    assert do_stuff.execute_in_process(
        {"ops": {"process_data_for_date": {"config": {"date": "2018-05-01"}}}},
    ).success

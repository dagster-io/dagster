from docs_snippets.guides.build.partitions_backfills.date_config_job import do_stuff


def test_do_stuff():
    assert do_stuff.execute_in_process(
        {"ops": {"process_data_for_date": {"config": {"date": "2018-05-01"}}}},
    ).success

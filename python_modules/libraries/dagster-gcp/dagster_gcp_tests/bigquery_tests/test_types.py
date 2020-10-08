from dagster_gcp.bigquery.types import _is_valid_dataset, _is_valid_table


def test_dataset():
    good_dataset_1 = "project.dataset"
    good_dataset_2 = "project-name.dataset_foo"
    good_dataset_3 = "project_name.dataset"
    good_dataset_4 = "numbers_are1.ok_to_use2"

    bad_dataset_1 = "project.hyphen-datasets-not-permitted"
    bad_dataset_2 = "project%%%special_chars@==_not_permitted.dataset"
    bad_dataset_3 = "project.special_chars@==_not_permitted"
    bad_dataset_4 = "a" * 1025 + ".long_project_names_not_permitted"
    bad_dataset_5 = "long_dataset_names_not_permitted." + "a" * 1025

    assert _is_valid_dataset(good_dataset_1)
    assert _is_valid_dataset(good_dataset_2)
    assert _is_valid_dataset(good_dataset_3)
    assert _is_valid_dataset(good_dataset_4)

    assert not _is_valid_dataset(bad_dataset_1)
    assert not _is_valid_dataset(bad_dataset_2)
    assert not _is_valid_dataset(bad_dataset_3)
    assert not _is_valid_dataset(bad_dataset_4)
    assert not _is_valid_dataset(bad_dataset_5)


def test_table():
    # note that tests above should cover most table cases also

    good_table_1 = "project.dataset.table"
    good_table_2 = "project.dataset_underscores.table_underscores"
    good_table_3 = "project-with-hyphens.dataset_with_underscores.table_with_underscores"
    good_table_4 = "dataset.date_partitioned$20190101"
    good_table_5 = "project.dataset.date_partitioned$20190101"

    bad_table_1 = "project.dataset.table-hyphens-not-allowed"
    bad_table_2 = "project.dataset.table@special@chars@not@allowed"
    bad_table_3 = "project.long_table_names_not_permitted." + "a" * 1025

    assert _is_valid_table(good_table_1)
    assert _is_valid_table(good_table_2)
    assert _is_valid_table(good_table_3)
    assert _is_valid_table(good_table_4)
    assert _is_valid_table(good_table_5)

    assert not _is_valid_table(bad_table_1)
    assert not _is_valid_table(bad_table_2)
    assert not _is_valid_table(bad_table_3)

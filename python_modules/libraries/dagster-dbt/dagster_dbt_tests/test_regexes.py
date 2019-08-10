from dagster_dbt import CREATE_TABLE_REGEX, CREATE_VIEW_REGEX

TEST_CREATE_VIEW = (
    '17:36:00 | 3 of 8 OK created view model '
    'dbt_alice.stg_customers................. [CREATE VIEW in 0.18s]'
)

TEST_CREATE_TABLE = (
    '17:36:01 | 4 of 8 OK created table model '
    'dbt_alice.order_payments............... [SELECT 99 in 0.07s]'
)


def test_match_view_model():
    m = CREATE_VIEW_REGEX.search(TEST_CREATE_VIEW)
    assert m
    schema = m.group(1)
    assert schema == 'dbt_alice'
    view = m.group(2)
    assert view == 'stg_customers'


def test_match_table_model():
    m = CREATE_TABLE_REGEX.search(TEST_CREATE_TABLE)
    assert m

    schema = m.group(1)
    assert schema == 'dbt_alice'
    table = m.group(2)
    assert table == 'order_payments'
    row_count = int(m.group(3))
    assert row_count == 99

from dagster_dbt import CREATE_TABLE_REGEX, CREATE_VIEW_REGEX, TEST_FAIL_REGEX, TEST_PASS_REGEX

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


TEST_PASS_LONG_STRING = (
    '13:55:22 | 1 of 20 PASS '
    'accepted_values_fct_orders_status__placed__shipped__completed__return_pending__returned '
    '[PASS in 0.05s]'
)


TEST_PASS_SHORT_STRING = (
    '13:55:22 | 7 of 20 PASS not_null_fct_orders_coupon_amount'
    '....................... [PASS in 0.04s]'
)

LONG_NAME = (
    'accepted_values_fct_orders_status__placed__shipped__completed__return_pending__returned'
)


def test_pass_long_string():
    m = TEST_PASS_REGEX.search(TEST_PASS_LONG_STRING)
    assert m
    assert m.group(1) == LONG_NAME


def test_pass_short_string():
    m = TEST_PASS_REGEX.search(TEST_PASS_SHORT_STRING)
    assert m
    assert m.group(1) == 'not_null_fct_orders_coupon_amount'


def test_fail():
    test_fail_text = (
        'FAIL 5 accepted_values_fct_orders_status__jdkfjkd............ [FAIL 5 in 0.05s]'
    )

    m = TEST_FAIL_REGEX.search(test_fail_text)
    assert m
    assert m.group(1) == '5'
    assert m.group(2) == 'accepted_values_fct_orders_status__jdkfjkd'

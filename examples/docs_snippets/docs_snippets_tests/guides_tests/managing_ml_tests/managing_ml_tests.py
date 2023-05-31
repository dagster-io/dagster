from docs_snippets.guides.dagster.managing_ml.managing_ml_code import my_data


def test_assets():
    result = materialize([my_data])
    assert result.success
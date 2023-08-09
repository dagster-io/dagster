EXAMPLE_TEXT = """
stocks_to_index:
  - ticker: MSFT
  - ticker: AAPL
  - ticker: GOOG
  - ticker: AMZN
  - ticker: META
  - ticker: NVDA
  - ticker: TSLA
index_strategy:
  type: weighted_average
forecast:
  days: 30
"""


from assets_yaml_dsl.stocks_dsl import assets_defs_from_stocks_dsl_document


import yaml


def test_stocks_dsl():
    stocks_dsl_document = yaml.safe_load(EXAMPLE_TEXT)
    assert stocks_dsl_document

    assets_defs = assets_defs_from_stocks_dsl_document(stocks_dsl_document)

    assets_defs
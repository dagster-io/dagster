from dagster import _check as check
from sqlglot import (
    Dialect,
    Dialects,
    expressions as exp,
)

bq = Dialects.BIGQUERY

custom_bigquery_dialect = check.not_none(Dialect.get(key=Dialects.BIGQUERY))
custom_bigquery_dialect_inst = custom_bigquery_dialect()

# Set the default value for the DISTINCT keyword in set operations to True.
# Right now, unions which don't specify UNIQUE or DISTINCT keywords lead to an error
# because sqlglot doesn't assume default behavior for bigquery set operations. Looker
# is OK with this behavior, so we're setting the default to True.
custom_bigquery_dialect_inst.SET_OP_DISTINCT_BY_DEFAULT = {
    **custom_bigquery_dialect_inst.SET_OP_DISTINCT_BY_DEFAULT,
    exp.Union: True,
}

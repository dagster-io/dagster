from dagster import materialize
from docs_snippets.concepts.assets.non_argument_deps import (
    shopping_list,
    sugary_cereals,
)


def test_non_argument_deps():
    materialize([shopping_list, sugary_cereals])

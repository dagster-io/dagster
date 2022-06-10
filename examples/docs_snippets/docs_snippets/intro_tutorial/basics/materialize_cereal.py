from doc_snippets.guides.dagster.asset_tutorial.serial_asset_graph import (
    cereals,
    nabisco_cereals,
)

# start_example

from dagster import materialize


if __name__ == "__main__":
    materialize([cereals, nabisco_cereals])

# end_example

# /// script
# dependencies = [
#   "dagster-pipes",
#   "cowsay",
# ]
# ///

import cowsay  # type: ignore
from dagster_pipes import PipesContext, open_dagster_pipes


def execute(context: PipesContext) -> None:
    context.report_asset_materialization(
        metadata={"foo": "bar", "cowsay": cowsay.get_output_string("cow", "hello world")}
    )


if __name__ == "__main__":
    with open_dagster_pipes() as pipes:
        execute(pipes)

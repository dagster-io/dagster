# /// script
# dependencies = [
#   "dagster-pipes",
#   "cowsay",
# ]
# ///
from dagster_pipes import PipesContext, open_dagster_pipes


def execute(context: PipesContext) -> None:
    import cowsay  # type: ignore

    context.report_asset_materialization(
        metadata={"foo": "bar", "cowsay": cowsay.get_output_string("cow", "hello world")}
    )


if __name__ == "__main__":
    with open_dagster_pipes() as pipes:
        execute(pipes)

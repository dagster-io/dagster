from dagster_pipes import (
    PipesDbfsContextLoader,
    PipesDbfsMessageWriter,
    open_dagster_pipes,
)

# ... existing code

if __name__ == "__main__":
    with open_dagster_pipes(
        context_loader=PipesDbfsContextLoader(),
        message_writer=PipesDbfsMessageWriter(),
    ) as pipes:
        # ... existing logic
        pipes.report_asset_materialization(
            asset_key="foo",
            metadata={"some_key": "some_value"},
            data_version="alpha",
        )

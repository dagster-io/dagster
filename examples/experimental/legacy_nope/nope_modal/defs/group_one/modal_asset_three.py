import modal  # type: ignore

app = modal.App("schrockn-project-pipes-kicktest")


def do_pandas_stuff() -> int:
    # we want this to execute in modal's cloud
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    # Add 1 to every element in column 'a'
    df["a"] = df["a"] + 1
    # Sum the values in column 'a'
    return df["a"].sum()


def image_with_pandas() -> modal.Image:
    return (
        modal.Image.debian_slim()
        .pip_install("uv")
        .run_commands("uv pip install --compile-bytecode --system pandas")
    )


@app.function(image=image_with_pandas())
def asset_three_on_modal() -> None:
    value = do_pandas_stuff()
    return {"value": str(value)}
    # print(f"Value: {value}")
    # print("did this work")


@app.local_entrypoint()
def main() -> None:
    from dagster_pipes import open_dagster_pipes

    with open_dagster_pipes() as pipes:
        pipes.log.info("This code is running on local.")
        metadata_returned = asset_three_on_modal.remote()
        pipes.report_asset_materialization(metadata_returned)

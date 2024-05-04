import modal  # type: ignore
app = modal.App("schrockn-project-pipes-kicktest")


@app.function()
def asset_two_on_modal() -> None:
    print("second asset")


@app.local_entrypoint()
def main() -> None:
    from dagster_pipes import open_dagster_pipes
    with open_dagster_pipes():
        asset_two_on_modal.remote()


if __name__ == "__main__":
    ...

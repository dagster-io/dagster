import dagster as dg


@dg.asset
def loaded_file() -> str:
    with open("path.txt") as file:
        return file.read()


# highlight-start
def test_loaded_file() -> None:
    assert loaded_file() == "contents"
    # highlight-end

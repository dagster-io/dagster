import dagster as dg


@dg.asset
def loaded_file() -> str:
    with open("path.txt") as file:
        return file.read()


@dg.asset
def processed_file(loaded_file: str) -> str:
    return loaded_file.strip()


# highlight-start
def test_processed_file() -> None:
    assert processed_file(" contents  ") == "contents"
    # highlight-end

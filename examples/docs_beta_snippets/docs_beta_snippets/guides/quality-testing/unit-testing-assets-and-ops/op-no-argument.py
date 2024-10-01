import dagster as dg


@dg.op
def load_file() -> str:
    with open("path.txt") as file:
        return file.read()


# highlight-start
def test_load_file() -> None:
    assert load_file() == "contents"
    # highlight-end

import dagster as dg


@dg.op
def process_file(loaded_file: str) -> str:
    return loaded_file.strip()


# highlight-start
def test_process_file() -> None:
    assert process_file(" contents  ") == "contents"
    # highlight-end

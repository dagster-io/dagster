# start_file
import dagster as dg


@dg.op
def process_file(loaded_file: str) -> str:
    return loaded_file.strip()


# end_file


# start_test
def test_process_file() -> None:
    assert process_file(" contents  ") == "contents"


# end_test

# start_file
import dagster as dg


@dg.op
def load_file() -> str:
    with open("path.txt") as file:
        return file.read()


# end_file


# start_test
def test_load_file() -> None:
    assert load_file() == "contents"


# end_test

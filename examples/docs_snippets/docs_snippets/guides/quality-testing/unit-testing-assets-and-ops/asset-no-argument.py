# start_file
import dagster as dg


@dg.asset
def loaded_file() -> str:
    with open("path.txt") as file:
        return file.read()


# end_file


# start_test
def test_loaded_file() -> None:
    assert loaded_file() == "contents"


# end_test

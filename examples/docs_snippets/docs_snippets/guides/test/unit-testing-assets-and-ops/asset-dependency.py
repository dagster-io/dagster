# start_file
import dagster as dg


@dg.asset
def loaded_file() -> str:
    with open("path.txt", encoding="utf-8") as file:
        return file.read()


@dg.asset
def processed_file(loaded_file: str) -> str:
    return loaded_file.strip()


# end_file


# start_test
def test_processed_file() -> None:
    assert processed_file(" contents  ") == "contents"


# end_test

# start_file
import dagster as dg


class FilepathConfig(dg.Config):
    path: str


@dg.op
def load_file(config: FilepathConfig) -> str:
    with open(config.path) as file:
        return file.read()


# end_file


# start_test
def test_load_file() -> None:
    assert load_file(FilepathConfig(path="path1.txt")) == "contents1"
    assert load_file(FilepathConfig(path="path2.txt")) == "contents2"


# end_test

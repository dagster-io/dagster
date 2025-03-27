import dagster as dg


class FilepathConfig(dg.Config):
    path: str


@dg.asset
def loaded_file(config: FilepathConfig) -> str:
    with open(config.path) as file:
        return file.read()


# highlight-start
def test_loaded_file() -> None:
    assert loaded_file(FilepathConfig(path="path1.txt")) == "contents1"
    assert loaded_file(FilepathConfig(path="path2.txt")) == "contents2"
    # highlight-end

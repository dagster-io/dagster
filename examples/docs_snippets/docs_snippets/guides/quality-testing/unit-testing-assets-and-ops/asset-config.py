from my_project.defs.assets import FilepathConfig, loaded_file


# highlight-start
def test_loaded_file() -> None:
    assert loaded_file(FilepathConfig(path="path1.txt")) == "contents1"
    assert loaded_file(FilepathConfig(path="path2.txt")) == "contents2"
    # highlight-end

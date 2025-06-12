from my_project.defs.assets import FilepathConfig, load_file


# highlight-start
def test_load_file() -> None:
    assert load_file(FilepathConfig(path="path1.txt")) == "contents1"
    assert load_file(FilepathConfig(path="path2.txt")) == "contents2"
    # highlight-end

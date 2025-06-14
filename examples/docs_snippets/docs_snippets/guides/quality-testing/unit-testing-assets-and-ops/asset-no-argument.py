from my_project.defs.assets import loaded_file


# highlight-start
def test_loaded_file() -> None:
    assert loaded_file() == "contents"
    # highlight-end

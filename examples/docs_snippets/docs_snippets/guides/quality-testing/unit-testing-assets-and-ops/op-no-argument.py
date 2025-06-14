from my_project.defs.assets import load_file


# highlight-start
def test_load_file() -> None:
    assert load_file() == "contents"
    # highlight-end

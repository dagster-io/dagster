from my_project.defs.assets import processed_file


# highlight-start
def test_processed_file() -> None:
    assert processed_file(" contents  ") == "contents"
    # highlight-end

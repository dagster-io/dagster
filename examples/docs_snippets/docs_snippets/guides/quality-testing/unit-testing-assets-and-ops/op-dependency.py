from my_project.defs.assets import process_file


# highlight-start
def test_process_file() -> None:
    assert process_file(" contents  ") == "contents"
    # highlight-end

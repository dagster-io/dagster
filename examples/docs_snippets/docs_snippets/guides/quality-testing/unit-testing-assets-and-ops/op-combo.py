from my_project.defs.assets import SeparatorConfig, process_file


# highlight-start
def test_process_file() -> None:
    assert (
        process_file(
            primary_file="abc",
            secondary_file="def",
            config=SeparatorConfig(separator=","),
        )
        == "abc,def"
    )
    # highlight-end

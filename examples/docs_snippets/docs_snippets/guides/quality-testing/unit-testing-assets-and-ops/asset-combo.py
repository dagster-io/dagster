from my_project.defs.assets import SeparatorConfig, processed_file


# highlight-start
def test_processed_file() -> None:
    assert (
        processed_file(
            primary_file="abc",
            secondary_file="def",
            config=SeparatorConfig(separator=","),
        )
        == "abc,def"
    )
    # highlight-end

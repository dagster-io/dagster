import dagster as dg


class SeparatorConfig(dg.Config):
    separator: str


@dg.op
def process_file(
    primary_file: str, secondary_file: str, config: SeparatorConfig
) -> str:
    return f"{primary_file}{config.separator}{secondary_file}"


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

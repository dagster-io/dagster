import pytest

from dagster._utils import snakecase


@pytest.mark.parametrize(
    "value, expected",
    [
        ("MyClassName", "my_class_name"),
        ("already_snake", "already_snake"),
        ("with-dashes", "with_dashes"),
        ("with spaces", "with_spaces"),
        ("foo123Bar", "foo123_bar"),
        # Each capital in a run gets its own underscore boundary.
        ("HTTPServer", "h_t_t_p_server"),
    ],
)
def test_snakecase(value, expected):
    assert snakecase(value) == expected

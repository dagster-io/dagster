from dagster._utils.names import (
    clean_name,
    clean_name_lower,
    clean_name_lower_with_dots,
)


def test_clean_name_replaces_invalid_characters_with_underscores():
    assert clean_name("foo bar-baz!") == "foo_bar_baz_"


def test_clean_name_collapses_runs_of_invalid_characters():
    # A run of invalid characters becomes a single underscore.
    assert clean_name("a  -  b") == "a_b"


def test_clean_name_preserves_existing_underscores_and_alphanumerics():
    assert clean_name("a__b9C") == "a__b9C"


def test_clean_name_treats_dot_as_invalid():
    assert clean_name("a.b") == "a_b"


def test_clean_name_on_empty_string():
    assert clean_name("") == ""


def test_clean_name_lower_lowercases_result():
    assert clean_name_lower("Foo Bar") == "foo_bar"


def test_clean_name_lower_still_cleans_invalid_characters():
    assert clean_name_lower("My-Asset!") == "my_asset_"


def test_clean_name_lower_with_dots_keeps_dots():
    assert clean_name_lower_with_dots("My.Asset Name!") == "my.asset_name_"


def test_clean_name_lower_with_dots_still_lowercases_and_cleans():
    assert clean_name_lower_with_dots("A B.C-D") == "a_b.c_d"

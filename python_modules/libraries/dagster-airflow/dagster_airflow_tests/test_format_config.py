import pytest
from dagster_airflow.format import format_dict_for_graphql

from dagster import check


def test_format_dict():
    with pytest.raises(check.CheckError):
        format_dict_for_graphql("")

    with pytest.raises(check.CheckError):
        format_dict_for_graphql(None)

    with pytest.raises(check.CheckError):
        format_dict_for_graphql([])

    with pytest.raises(check.CheckError):
        format_dict_for_graphql(3)

    assert format_dict_for_graphql({}) == "{\n}\n"

    assert format_dict_for_graphql({"foo": "bar"}) == '{\n  foo: "bar"\n}\n'

    assert (
        format_dict_for_graphql({"foo": "bar", "baz": "quux"})
        == '{\n  baz: "quux",\n  foo: "bar"\n}\n'
    )

    assert format_dict_for_graphql({"foo": {"bar": "baz", "quux": "bip"}}) == (
        "{\n" "  foo: {\n" '    bar: "baz",\n' '    quux: "bip"\n' "  }\n" "}\n"
    )

    assert format_dict_for_graphql({"foo": {"bar": 3, "quux": "bip"}}) == (
        "{\n" "  foo: {\n" "    bar: 3,\n" '    quux: "bip"\n' "  }\n" "}\n"
    )

    assert format_dict_for_graphql({"foo": {"bar": {"baz": {"quux": "bip", "bop": "boop"}}}}) == (
        "{\n"
        "  foo: {\n"
        "    bar: {\n"
        "      baz: {\n"
        '        bop: "boop",\n'
        '        quux: "bip"\n'
        "      }\n"
        "    }\n"
        "  }\n"
        "}\n"
    )

    assert format_dict_for_graphql({"foo": {"bar": ["baz", "quux"]}}) == (
        "{\n" "  foo: {\n" "    bar: [\n" '      "baz",\n' '      "quux"\n' "    ]\n" "  }\n" "}\n"
    )

    assert format_dict_for_graphql({"foo": {"bar": ["baz", {"quux": "ruux"}]}}) == (
        "{\n"
        "  foo: {\n"
        "    bar: [\n"
        '      "baz",\n'
        "      {\n"
        '        quux: "ruux"\n'
        "      }\n"
        "    ]\n"
        "  }\n"
        "}\n"
    )

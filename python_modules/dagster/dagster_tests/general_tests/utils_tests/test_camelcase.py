from dagster.utils import camelcase


def test_camelcase():
    assert camelcase("foo") == "Foo"
    assert camelcase("foo_bar") == "FooBar"
    assert camelcase("foo.bar") == "FooBar"
    assert camelcase("foo-bar") == "FooBar"
    assert camelcase("") == ""

from dagster._annotations import (
    deprecated,
    experimental,
    is_deprecated,
    is_experimental,
    is_public,
    public,
)


def test_public_annotation():
    class Foo:
        @public
        def bar(self):
            pass

    assert is_public(Foo.bar)


def test_deprecated():
    class Foo:
        @deprecated
        def bar(self):
            pass

    assert is_deprecated(Foo.bar)


def test_experimental():
    class Foo:
        @experimental
        def bar(self):
            pass

    assert is_experimental(Foo.bar)

import re
import sys
import warnings
from abc import abstractmethod
from typing import Annotated, NamedTuple, get_type_hints

import pytest
from dagster import BetaWarning, PreviewWarning, SupersessionWarning, resource
from dagster._annotations import (
    PUBLIC,
    PublicAttr,
    beta,
    beta_param,
    deprecated,
    deprecated_param,
    get_beta_info,
    get_deprecated_info,
    get_preview_info,
    get_superseded_info,
    hidden_param,
    is_beta,
    is_beta_param,
    is_deprecated,
    is_deprecated_param,
    is_preview,
    is_public,
    is_superseded,
    only_allow_hidden_params_in_kwargs,
    preview,
    public,
    superseded,
)
from dagster._check import CheckError

from dagster_tests.general_tests.utils_tests.utils import assert_no_warnings


def compose_decorators(*decorators):
    def _decorator(fn):
        for decorator in reversed(decorators):
            fn = decorator(fn)
        return fn

    return _decorator


# ########################
# ##### PUBLIC
# ########################


def test_public_method():
    class Foo:
        @public
        def bar(self):
            pass

    assert is_public(Foo.bar)


@pytest.mark.parametrize(
    "decorators",
    [
        (public, property),
        (property, public),
        (public, staticmethod),
        (staticmethod, public),
        (public, classmethod),
        (classmethod, public),
        (public, abstractmethod),
        (abstractmethod, public),
    ],
    ids=[
        "public-property",
        "property-public",
        "public-staticmethod",
        "staticmethod-public",
        "public-classmethod",
        "classmethod-public",
        "public-abstractmethod",
        "abstractmethod-public",
    ],
)
def test_public_multi_decorator(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self):
            pass

    assert is_public(Foo.__dict__["bar"])  # __dict__ for descriptor access


def test_public_attribute():
    class Foo(NamedTuple("_Foo", [("bar", PublicAttr[int])])):
        pass

    hints = (
        get_type_hints(Foo, include_extras=True)
        if sys.version_info >= (3, 9)
        else get_type_hints(Foo)
    )
    assert hints["bar"] == Annotated[int, PUBLIC]


# ########################
# ##### DEPRECATED
# ########################

# In the below tests, we don't check the category at the start of the error message ("Function",
# "Class method", "Property", etc) because this unfortunately depends on the ordering of the
# decorators:
#
# @deprecated
# @property
# def foo(self):  # "Property `foo` is deprecated..."

# @deprecated
# @property
# def foo(self):  # "Function `foo` is deprecated..."

deprecated_bound = deprecated(breaking_version="2.0", additional_warn_text="foo")


def test_deprecated_method():
    class Foo:
        @deprecated_bound
        def bar(self):
            pass

    assert is_deprecated(Foo.bar)
    assert get_deprecated_info(Foo.bar).breaking_version == "2.0"

    with pytest.warns(
        DeprecationWarning,
        match=r"Function `[^`]+Foo.bar` is deprecated and will be removed in 2.0",
    ):
        Foo().bar()


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_bound, property),
        (property, deprecated_bound),
    ],
    ids=[
        "deprecated-property",
        "property-deprecated",
    ],
)
def test_deprecated_property(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self):
            return 1

    assert is_deprecated(Foo.__dict__["bar"])  # __dict__ access to get property

    with pytest.warns(
        DeprecationWarning, match=r"`[^`]+Foo.bar` is deprecated and will be removed in 2.0"
    ) as warning:
        assert Foo().bar
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_bound, staticmethod),
        (staticmethod, deprecated_bound),
    ],
    ids=[
        "deprecated-staticmethod",
        "staticmethod-deprecated",
    ],
)
def test_deprecated_staticmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar():
            pass

    assert is_deprecated(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(
        DeprecationWarning, match=r"`[^`]+Foo.bar` is deprecated and will be removed in 2.0"
    ) as warning:
        Foo.bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_bound, classmethod),
        (classmethod, deprecated_bound),
    ],
    ids=[
        "deprecated-classmethod",
        "classmethod-deprecated",
    ],
)
def test_deprecated_classmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(cls):
            pass

    assert is_deprecated(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(
        DeprecationWarning, match=r"`[^`]+Foo.bar` is deprecated and will be removed in 2.0"
    ) as warning:
        Foo.bar()  # pyright: ignore[reportCallIssue]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_bound, abstractmethod),
        (abstractmethod, deprecated_bound),
    ],
    ids=[
        "deprecated-abstractmethod",
        "abstractmethod-deprecated",
    ],
)
def test_deprecated_abstractmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self): ...

    assert is_deprecated(Foo.bar)  # __dict__ access to get descriptor


def test_deprecated_class():
    @deprecated_bound
    class Foo:
        def bar(self): ...

    assert is_deprecated(Foo)

    with pytest.warns(
        DeprecationWarning, match=r"Class `[^`]+Foo` is deprecated and will be removed in 2.0"
    ) as warning:
        Foo()
    assert warning[0].filename.endswith("test_annotations.py")


def test_deprecated_namedtuple_class():
    @deprecated_bound
    class Foo(NamedTuple("_", [("bar", str)])):
        pass

    with pytest.warns(
        DeprecationWarning, match=r"Class `[^`]+Foo` is deprecated and will be removed in 2.0"
    ) as warning:
        Foo(bar="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_deprecated_resource():
    @deprecated_bound
    @resource
    def foo(): ...

    assert is_deprecated(foo)

    with pytest.warns(
        DeprecationWarning,
        match=r"Dagster resource `[^`]+foo` is deprecated and will be removed in 2.0",
    ) as warning:
        foo()
        assert warning[0].filename.endswith("test_annotations.py")


def test_deprecated_suppress_warning():
    @deprecated(breaking_version="2.0", additional_warn_text="foo", emit_runtime_warning=False)
    def foo():
        pass

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        foo()


# ########################
# ##### DEPRECATED PARAM
# ########################

deprecated_param_bound = deprecated_param(param="baz", breaking_version="2.0")


def test_deprecated_param_method():
    class Foo:
        @deprecated_param_bound
        def bar(self, baz=None):
            pass

    assert is_deprecated_param(Foo.bar, "baz")

    with pytest.warns(
        DeprecationWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.bar` is deprecated"
    ) as warning:
        Foo().bar(baz="ok")
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_param_bound, staticmethod),
        (staticmethod, deprecated_param_bound),
    ],
    ids=[
        "deprecated_param-staticmethod",
        "staticmethod-deprecated_param",
    ],
)
def test_deprecated_param_staticmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(baz=None):
            pass

    assert is_deprecated_param(Foo.__dict__["bar"], "baz")  # __dict__ to access descriptor

    with pytest.warns(
        DeprecationWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.bar` is deprecated"
    ) as warning:
        Foo.bar(baz="ok")  # pyright: ignore[reportArgumentType]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_param_bound, classmethod),
        (classmethod, deprecated_param_bound),
    ],
    ids=[
        "deprecated_param-classmethod",
        "classmethod-deprecated_param",
    ],
)
def test_deprecated_param_classmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(cls, baz=None):
            pass

    assert is_deprecated_param(Foo.__dict__["bar"], "baz")  # __dict__ to access descriptor

    with pytest.warns(
        DeprecationWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.bar` is deprecated"
    ) as warning:
        Foo.bar(baz="ok")  # pyright: ignore[reportCallIssue]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (deprecated_param_bound, abstractmethod),
        (abstractmethod, deprecated_param_bound),
    ],
    ids=[
        "deprecated_param-abstractmethod",
        "abstractmethod-deprecated_param",
    ],
)
def test_deprecated_param_abstractmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self, baz=None): ...

    assert is_deprecated_param(Foo.bar, "baz")


def test_deprecated_param_class():
    @deprecated_param_bound
    class Foo:
        def __init__(self, baz=None): ...

    assert is_deprecated_param(Foo, "baz")

    with pytest.warns(
        DeprecationWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.__init__` is deprecated"
    ) as warning:
        Foo(baz="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_deprecated_param_named_tuple_class():
    @deprecated_param_bound
    class Foo(NamedTuple("_", [("baz", str)])):
        def __new__(cls, baz=None): ...

    assert is_deprecated_param(Foo, "baz")

    with pytest.warns(
        DeprecationWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.__init__` is deprecated"
    ) as warning:
        Foo(baz="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_invalid_deprecated_param():
    with pytest.raises(CheckError, match="undefined parameter"):

        @deprecated_param_bound
        def foo():
            pass


########################
##### PREVIEW
########################


def test_preview_method():
    class Foo:
        @preview(additional_warn_text="baz")
        def bar(self):
            pass

    assert is_preview(Foo.bar)
    assert get_preview_info(Foo.bar).additional_warn_text == "baz"

    with pytest.warns(PreviewWarning, match=r"`[^`]+Foo.bar` is currently in preview") as warning:
        Foo().bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (preview, property),
        (property, preview),
    ],
    ids=[
        "preview-property",
        "property-preview",
    ],
)
def test_preview_property(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self):
            return 1

    assert is_preview(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(PreviewWarning, match=r"`[^`]+Foo.bar` is currently in preview") as warning:
        assert Foo().bar
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (preview, staticmethod),
        (staticmethod, preview),
    ],
    ids=[
        "preview-staticmethod",
        "staticmethod-preview",
    ],
)
def test_preview_staticmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar():
            pass

    assert is_preview(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(PreviewWarning, match=r"`[^`]+Foo.bar` is currently in preview") as warning:
        Foo.bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (preview, classmethod),
        (classmethod, preview),
    ],
    ids=[
        "preview-classmethod",
        "classmethod-preview",
    ],
)
def test_preview_classmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(cls):
            pass

    assert is_preview(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(PreviewWarning, match=r"`[^`]+Foo.bar` is currently in preview") as warning:
        Foo.bar()  # pyright: ignore[reportCallIssue]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (preview, abstractmethod),
        (abstractmethod, preview),
    ],
    ids=[
        "preview-abstractmethod",
        "abstractmethod-preview",
    ],
)
def test_preview_abstractmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self): ...

    assert is_preview(Foo.bar)


def test_preview_class():
    @preview
    class Foo:
        def bar(self): ...

    assert is_preview(Foo)

    with pytest.warns(PreviewWarning, match=r"`[^`]+Foo` is currently in preview") as warning:
        Foo()
    assert warning[0].filename.endswith("test_annotations.py")


def test_preview_class_with_methods():
    @preview
    class PreviewClass:
        def __init__(self, salutation="hello"):
            self.salutation = salutation

        def hello(self, name):
            return f"{self.salutation} {name}"

    @preview
    class PreviewClassWithPreviewFunction(PreviewClass):
        def __init__(self, sendoff="goodbye", **kwargs):
            self.sendoff = sendoff
            super().__init__(**kwargs)

        @preview
        def goodbye(self, name):
            return f"{self.sendoff} {name}"

    with pytest.warns(
        PreviewWarning,
        match=r"`[^`]+PreviewClass` is currently in preview",
    ):
        preview_class = PreviewClass(salutation="howdy")

    with assert_no_warnings():
        assert preview_class.hello("dagster") == "howdy dagster"

    with pytest.warns(
        PreviewWarning,
        match=r"Class `[^`]+PreviewClassWithPreviewFunction` is currently in preview",
    ):
        preview_class_with_preview_function = PreviewClassWithPreviewFunction()

    with assert_no_warnings():
        assert preview_class_with_preview_function.hello("dagster") == "hello dagster"

    with pytest.warns(
        PreviewWarning,
        match=r"Function `[^`]+goodbye` currently in preview",
    ):
        assert preview_class_with_preview_function.goodbye("dagster") == "goodbye dagster"

    @preview
    class PreviewNamedTupleClass(NamedTuple("_", [("salutation", str)])):
        pass

    with pytest.warns(
        PreviewWarning,
        match=r"`[^`]+PreviewNamedTupleClass` is currently in preview",
    ):
        assert PreviewNamedTupleClass(salutation="howdy").salutation == "howdy"


def test_preview_namedtuple_class():
    @preview
    class Foo(NamedTuple("_", [("bar", str)])):
        pass

    with pytest.warns(PreviewWarning, match=r"Class `[^`]+Foo` is currently in preview") as warning:
        Foo(bar="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_preview_resource():
    @preview
    @resource
    def foo(): ...

    assert is_preview(foo)

    with pytest.warns(
        PreviewWarning,
        match=r"Dagster resource `[^`]+foo` is currently in preview",
    ) as warning:
        foo()
        assert warning[0].filename.endswith("test_annotations.py")


########################
##### BETA
########################


def test_beta_method():
    class Foo:
        @beta(additional_warn_text="baz")
        def bar(self):
            pass

    assert is_beta(Foo.bar)
    assert get_beta_info(Foo.bar).additional_warn_text == "baz"

    with pytest.warns(BetaWarning, match=r"`[^`]+Foo.bar` is currently in beta") as warning:
        Foo().bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta, property),
        (property, beta),
    ],
    ids=[
        "beta-property",
        "property-beta",
    ],
)
def test_beta_property(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self):
            return 1

    assert is_beta(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(BetaWarning, match=r"`[^`]+Foo.bar` is currently in beta") as warning:
        assert Foo().bar
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta, staticmethod),
        (staticmethod, beta),
    ],
    ids=[
        "beta-staticmethod",
        "staticmethod-beta",
    ],
)
def test_beta_staticmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar():
            pass

    assert is_beta(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(BetaWarning, match=r"`[^`]+Foo.bar` is currently in beta") as warning:
        Foo.bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta, classmethod),
        (classmethod, beta),
    ],
    ids=[
        "beta-classmethod",
        "classmethod-beta",
    ],
)
def test_beta_classmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(cls):
            pass

    assert is_beta(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(BetaWarning, match=r"`[^`]+Foo.bar` is currently in beta") as warning:
        Foo.bar()  # pyright: ignore[reportCallIssue]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta, abstractmethod),
        (abstractmethod, beta),
    ],
    ids=[
        "beta-abstractmethod",
        "abstractmethod-beta",
    ],
)
def test_beta_abstractmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self): ...

    assert is_beta(Foo.bar)


def test_beta_class():
    @beta
    class Foo:
        def bar(self): ...

    assert is_beta(Foo)

    with pytest.warns(BetaWarning, match=r"`[^`]+Foo` is currently in beta") as warning:
        Foo()
    assert warning[0].filename.endswith("test_annotations.py")


def test_beta_class_with_methods():
    @beta
    class BetaClass:
        def __init__(self, salutation="hello"):
            self.salutation = salutation

        def hello(self, name):
            return f"{self.salutation} {name}"

    @beta
    class BetaClassWithBetaFunction(BetaClass):
        def __init__(self, sendoff="goodbye", **kwargs):
            self.sendoff = sendoff
            super().__init__(**kwargs)

        @beta
        def goodbye(self, name):
            return f"{self.sendoff} {name}"

    with pytest.warns(
        BetaWarning,
        match=r"`[^`]+BetaClass` is currently in beta",
    ):
        beta_class = BetaClass(salutation="howdy")

    with assert_no_warnings():
        assert beta_class.hello("dagster") == "howdy dagster"

    with pytest.warns(
        BetaWarning,
        match=r"Class `[^`]+BetaClassWithBetaFunction` is currently in beta",
    ):
        beta_class_with_beta_function = BetaClassWithBetaFunction()

    with assert_no_warnings():
        assert beta_class_with_beta_function.hello("dagster") == "hello dagster"

    with pytest.warns(
        BetaWarning,
        match=r"Function `[^`]+goodbye` is currently in beta",
    ):
        assert beta_class_with_beta_function.goodbye("dagster") == "goodbye dagster"

    @beta
    class BetaNamedTupleClass(NamedTuple("_", [("salutation", str)])):
        pass

    with pytest.warns(
        BetaWarning,
        match=r"`[^`]+BetaNamedTupleClass` is currently in beta",
    ):
        assert BetaNamedTupleClass(salutation="howdy").salutation == "howdy"


def test_beta_namedtuple_class():
    @beta
    class Foo(NamedTuple("_", [("bar", str)])):
        pass

    with pytest.warns(BetaWarning, match=r"Class `[^`]+Foo` is currently in beta") as warning:
        Foo(bar="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_beta_resource():
    @beta
    @resource
    def foo(): ...

    assert is_beta(foo)

    with pytest.warns(
        BetaWarning,
        match=r"Dagster resource `[^`]+foo` is currently in beta",
    ) as warning:
        foo()
        assert warning[0].filename.endswith("test_annotations.py")


# ########################
# ##### BETA PARAM
# ########################


def test_beta_param_method():
    class Foo:
        @beta_param(param="baz")
        def bar(self, baz=None):
            pass

    assert is_beta_param(Foo.bar, "baz")

    with pytest.warns(
        BetaWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.bar` is currently in beta"
    ) as warning:
        Foo().bar(baz="ok")
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta_param(param="baz"), staticmethod),
        (staticmethod, beta_param(param="baz")),
    ],
    ids=[
        "beta_param-staticmethod",
        "staticmethod-beta_param",
    ],
)
def test_beta_param_staticmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(baz=None):
            pass

    assert is_beta_param(Foo.__dict__["bar"], "baz")  # __dict__ to access descriptor

    with pytest.warns(
        BetaWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.bar` is currently in beta"
    ) as warning:
        Foo.bar(baz="ok")  # pyright: ignore[reportArgumentType]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta_param(param="baz"), classmethod),
        (classmethod, beta_param(param="baz")),
    ],
    ids=[
        "beta_param-classmethod",
        "classmethod-beta_param",
    ],
)
def test_beta_param_classmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(cls, baz=None):
            pass

    assert is_beta_param(Foo.__dict__["bar"], "baz")  # __dict__ to access descriptor

    with pytest.warns(
        BetaWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.bar` is currently in beta"
    ) as warning:
        Foo.bar(baz="ok")  # pyright: ignore[reportCallIssue]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (beta_param(param="baz"), abstractmethod),
        (abstractmethod, beta_param(param="baz")),
    ],
    ids=[
        "beta-abstractmethod",
        "abstractmethod-beta",
    ],
)
def test_beta_param_abstractmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self, baz=None): ...

    assert is_beta_param(Foo.bar, "baz")


def test_beta_param_class():
    @beta_param(param="baz")
    class Foo:
        def __init__(self, baz=None): ...

    assert is_beta_param(Foo, "baz")

    with pytest.warns(
        BetaWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.__init__` is currently in beta"
    ) as warning:
        Foo(baz="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_beta_param_named_tuple_class():
    @beta_param(param="baz")
    class Foo(NamedTuple("_", [("baz", str)])):
        def __new__(cls, baz=None): ...

    assert is_beta_param(Foo, "baz")

    with pytest.warns(
        BetaWarning, match=r"Parameter `baz` of [^`]+`[^`]+Foo.__init__` is currently in beta"
    ) as warning:
        Foo(baz="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_invalid_beta_param():
    with pytest.raises(CheckError, match="undefined parameter"):

        @beta_param(param="baz")
        def foo():
            pass


########################
##### SUPERSEDED
########################


def test_superseded_method():
    class Foo:
        @superseded(additional_warn_text="baz")
        def bar(self):
            pass

    assert is_superseded(Foo.bar)
    assert get_superseded_info(Foo.bar).additional_warn_text == "baz"

    with pytest.warns(SupersessionWarning, match=r"`[^`]+Foo.bar` is superseded") as warning:
        Foo().bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (superseded, property),
        (property, superseded),
    ],
    ids=[
        "superseded-property",
        "property-superseded",
    ],
)
def test_superseded_property(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self):
            return 1

    assert is_superseded(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(SupersessionWarning, match=r"`[^`]+Foo.bar` is superseded") as warning:
        assert Foo().bar
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (superseded, staticmethod),
        (staticmethod, superseded),
    ],
    ids=[
        "superseded-staticmethod",
        "staticmethod-superseded",
    ],
)
def test_superseded_staticmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar():
            pass

    assert is_superseded(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(SupersessionWarning, match=r"`[^`]+Foo.bar` is superseded") as warning:
        Foo.bar()
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (superseded, classmethod),
        (classmethod, superseded),
    ],
    ids=[
        "superseded-classmethod",
        "classmethod-superseded",
    ],
)
def test_superseded_classmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(cls):
            pass

    assert is_superseded(Foo.__dict__["bar"])  # __dict__ access to get descriptor

    with pytest.warns(SupersessionWarning, match=r"`[^`]+Foo.bar` is superseded") as warning:
        Foo.bar()  # pyright: ignore[reportCallIssue]
    assert warning[0].filename.endswith("test_annotations.py")


@pytest.mark.parametrize(
    "decorators",
    [
        (superseded, abstractmethod),
        (abstractmethod, superseded),
    ],
    ids=[
        "superseded-abstractmethod",
        "abstractmethod-superseded",
    ],
)
def test_superseded_abstractmethod(decorators):
    class Foo:
        @compose_decorators(*decorators)
        def bar(self): ...

    assert is_superseded(Foo.bar)


def test_superseded_class():
    @superseded
    class Foo:
        def bar(self): ...

    assert is_superseded(Foo)

    with pytest.warns(SupersessionWarning, match=r"`[^`]+Foo` is superseded") as warning:
        Foo()
    assert warning[0].filename.endswith("test_annotations.py")


def test_superseded_class_with_methods():
    @superseded
    class SupersededClass:
        def __init__(self, salutation="hello"):
            self.salutation = salutation

        def hello(self, name):
            return f"{self.salutation} {name}"

    @superseded
    class SupersededClassWithSupersededFunction(SupersededClass):
        def __init__(self, sendoff="goodbye", **kwargs):
            self.sendoff = sendoff
            super().__init__(**kwargs)

        @superseded
        def goodbye(self, name):
            return f"{self.sendoff} {name}"

    with pytest.warns(
        SupersessionWarning,
        match=r"`[^`]+SupersededClass` is superseded",
    ):
        superseded_class = SupersededClass(salutation="howdy")

    with assert_no_warnings():
        assert superseded_class.hello("dagster") == "howdy dagster"

    with pytest.warns(
        SupersessionWarning,
        match=r"Class `[^`]+SupersededClassWithSupersededFunction` is superseded",
    ):
        superseded_class_with_superseded_function = SupersededClassWithSupersededFunction()

    with assert_no_warnings():
        assert superseded_class_with_superseded_function.hello("dagster") == "hello dagster"

    with pytest.warns(
        SupersessionWarning,
        match=r"Function `[^`]+goodbye` is superseded",
    ):
        assert superseded_class_with_superseded_function.goodbye("dagster") == "goodbye dagster"

    @superseded
    class SupersededNamedTupleClass(NamedTuple("_", [("salutation", str)])):
        pass

    with pytest.warns(
        SupersessionWarning,
        match=r"`[^`]+SupersededNamedTupleClass` is superseded",
    ):
        assert SupersededNamedTupleClass(salutation="howdy").salutation == "howdy"


def test_superseded_namedtuple_class():
    @superseded
    class Foo(NamedTuple("_", [("bar", str)])):
        pass

    with pytest.warns(SupersessionWarning, match=r"Class `[^`]+Foo` is superseded") as warning:
        Foo(bar="ok")
    assert warning[0].filename.endswith("test_annotations.py")


def test_superseded_resource():
    @superseded
    @resource
    def foo(): ...

    assert is_superseded(foo)

    with pytest.warns(
        SupersessionWarning,
        match=r"Dagster resource `[^`]+foo` is superseded",
    ) as warning:
        foo()
        assert warning[0].filename.endswith("test_annotations.py")


# ########################
# ##### OTHER
# ########################


def test_all_annotations():
    @public
    @deprecated(breaking_version="2.0", additional_warn_text="foo")
    @superseded
    @beta
    @preview
    def foo():
        pass

    assert is_public(foo)
    assert is_deprecated(foo)
    assert is_preview(foo)
    assert is_beta(foo)
    assert is_superseded(foo)

    with warnings.catch_warnings(record=True) as all_warnings:
        warnings.simplefilter("always")
        foo()

    exp = next(warning for warning in all_warnings if warning.category == PreviewWarning)
    assert re.search(r"`[^`]+foo`", str(exp.message))

    exp = next(warning for warning in all_warnings if warning.category == BetaWarning)
    assert re.search(r"`[^`]+foo`", str(exp.message))

    dep = next(warning for warning in all_warnings if warning.category == SupersessionWarning)
    assert re.search(r"`[^`]+foo` is superseded", str(dep.message))

    dep = next(warning for warning in all_warnings if warning.category == DeprecationWarning)
    assert re.search(r"`[^`]+foo` is deprecated", str(dep.message))


def test_hidden_annotations() -> None:
    @hidden_param(param="baz", breaking_version="2.0")
    def with_hidden_args(**kwargs) -> bool:
        only_allow_hidden_params_in_kwargs(with_hidden_args, kwargs)
        return True

    assert with_hidden_args(baz="foo")
    with pytest.raises(
        TypeError,
        match="with_hidden_args got an unexpected keyword argument 'does_not_exist'",
    ):
        with_hidden_args(does_not_exist="foo")

    with pytest.raises(
        CheckError,
        match="Invariant failed. Description: Attempted to mark undefined parameter `baz` deprecated.",
    ):

        @deprecated_param(param="baz", breaking_version="2.0")
        def incorrectly_annotated(**kwargs) -> bool:
            raise NotImplementedError("This function should not be called")

    def vanilla_func(**kwargs) -> bool:
        only_allow_hidden_params_in_kwargs(vanilla_func, kwargs)
        return True

    assert vanilla_func()
    with pytest.raises(
        TypeError,
        match="vanilla_func got an unexpected keyword argument 'hidden_param'",
    ):
        vanilla_func(hidden_param="foo")

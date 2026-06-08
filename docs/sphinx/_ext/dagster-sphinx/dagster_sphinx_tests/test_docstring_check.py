import pytest
from dagster_sphinx import check_public_method_has_docstring


def test_missing_docstring_raises() -> None:
    def no_doc():
        pass

    # Regression guard: every object has a `__doc__` attribute (defaulting to
    # None), so a `hasattr(obj, "__doc__")` check never fires. The check must
    # inspect the docstring's *value*.
    with pytest.raises(Exception, match="Docstring not found"):
        check_public_method_has_docstring(None, "no_doc", no_doc)


def test_present_docstring_passes() -> None:
    def has_doc():
        """A docstring."""

    check_public_method_has_docstring(None, "has_doc", has_doc)


def test_empty_docstring_raises() -> None:
    def empty_doc():
        """"""  # noqa: D419 - intentionally empty; exercises the check

    with pytest.raises(Exception, match="Docstring not found"):
        check_public_method_has_docstring(None, "empty_doc", empty_doc)


def test_init_is_exempt() -> None:
    def no_doc():
        pass

    # __init__ is intentionally exempt from the docstring requirement.
    check_public_method_has_docstring(None, "__init__", no_doc)

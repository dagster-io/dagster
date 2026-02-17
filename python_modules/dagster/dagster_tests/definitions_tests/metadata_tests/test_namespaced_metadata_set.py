from typing import Optional

import dagster as dg
import pytest
from dagster._check import CheckError
from dagster._core.definitions.metadata import NamespacedMetadataSet
from pydantic import ValidationError


def test_extract_primitive_coercion():
    class MyMetadataSet(NamespacedMetadataSet):
        primitive_int: Optional[int] = None
        primitive_float: Optional[float] = None
        int_metadata_value: Optional[dg.IntMetadataValue] = None
        url_metadata_value: Optional[dg.UrlMetadataValue] = None
        url_or_str_metadata_value: Optional[dg.UrlMetadataValue | str] = None
        url_or_str_order_reversed_metadata_value: Optional[str | dg.UrlMetadataValue] = None

        @classmethod
        def namespace(cls) -> str:
            return "foo"

    assert MyMetadataSet.extract({"foo/primitive_int": 5}).primitive_int == 5
    assert MyMetadataSet.extract({"foo/primitive_float": 5}).primitive_float == 5
    assert MyMetadataSet.extract({"foo/primitive_int": dg.IntMetadataValue(5)}).primitive_int == 5
    assert (
        MyMetadataSet.extract({"foo/primitive_float": dg.FloatMetadataValue(5.0)}).primitive_float
        == 5
    )
    assert MyMetadataSet.extract(
        {"foo/int_metadata_value": dg.IntMetadataValue(5)}
    ).int_metadata_value == dg.IntMetadataValue(5)

    assert MyMetadataSet.extract(
        {"foo/url_or_str_metadata_value": dg.UrlMetadataValue("dagster.io")}
    ).url_or_str_metadata_value == dg.UrlMetadataValue("dagster.io")
    assert (
        MyMetadataSet.extract(
            {"foo/url_or_str_metadata_value": "dagster.io"}
        ).url_or_str_metadata_value
        == "dagster.io"
    )

    assert MyMetadataSet.extract(
        {"foo/url_or_str_order_reversed_metadata_value": dg.UrlMetadataValue("dagster.io")}
    ).url_or_str_order_reversed_metadata_value == dg.UrlMetadataValue("dagster.io")
    assert (
        MyMetadataSet.extract(
            {"foo/url_or_str_order_reversed_metadata_value": "dagster.io"}
        ).url_or_str_order_reversed_metadata_value
        == "dagster.io"
    )

    with pytest.raises(ValidationError):
        MyMetadataSet.extract({"foo/int_metadata_value": 5})


def test_unsupported_type_annotations():
    class MyClass: ...

    class MyMetadataSet(NamespacedMetadataSet):
        unsupported: Optional[MyClass] = None

        @classmethod
        def namespace(cls) -> str:
            return "foo"

    with pytest.raises(
        CheckError,
        match=r"Type annotation for field 'unsupported' includes invalid metadata type\(s\).+MyClass",
    ):
        MyMetadataSet(unsupported=MyClass())

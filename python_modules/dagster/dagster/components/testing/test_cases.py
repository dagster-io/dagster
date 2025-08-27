from typing import Callable

from dagster_shared.merger import deep_merge_dicts

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.partitions.definition import StaticPartitionsDefinition

"""Testing utilities for components."""

from typing import Any, NamedTuple, Optional

# Unfortunate hack - we only use this util in pytest tests, we just drop in a no-op
# implementation if pytest is not installed.
try:
    import pytest  # type: ignore
except ImportError:

    class pytest:
        @staticmethod
        def fixture(*args, **kwargs) -> Callable:
            def wrapper(fn):
                return fn

            return wrapper


class TranslationTestCase(NamedTuple):
    name: str
    attributes: dict[str, Any]
    assertion: Callable[[AssetSpec], bool]
    key_modifier: Optional[Callable[[AssetKey], AssetKey]] = None


test_cases = [
    TranslationTestCase(
        name="group_name",
        attributes={"group_name": "group"},
        assertion=lambda asset_spec: asset_spec.group_name == "group",
    ),
    TranslationTestCase(
        name="owners",
        attributes={"owners": ["team:analytics"]},
        assertion=lambda asset_spec: asset_spec.owners == ["team:analytics"],
    ),
    TranslationTestCase(
        name="tags",
        attributes={"tags": {"foo": "bar"}},
        assertion=lambda asset_spec: asset_spec.tags.get("foo") == "bar",
    ),
    TranslationTestCase(
        name="kinds",
        attributes={"kinds": ["snowflake", "dbt"]},
        assertion=lambda asset_spec: "snowflake" in asset_spec.kinds and "dbt" in asset_spec.kinds,
    ),
    TranslationTestCase(
        name="tags-and-kinds",
        attributes={"tags": {"foo": "bar"}, "kinds": ["snowflake", "dbt"]},
        assertion=lambda asset_spec: "snowflake" in asset_spec.kinds
        and "dbt" in asset_spec.kinds
        and asset_spec.tags.get("foo") == "bar",
    ),
    TranslationTestCase(
        name="code-version",
        attributes={"code_version": "1"},
        assertion=lambda asset_spec: asset_spec.code_version == "1",
    ),
    TranslationTestCase(
        name="description",
        attributes={"description": "some description"},
        assertion=lambda asset_spec: asset_spec.description == "some description",
    ),
    TranslationTestCase(
        name="metadata",
        attributes={"metadata": {"foo": "bar"}},
        assertion=lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
    ),
    TranslationTestCase(
        name="deps",
        attributes={"deps": ["nonexistent"]},
        assertion=lambda asset_spec: len(asset_spec.deps) == 1
        and asset_spec.deps[0].asset_key == AssetKey("nonexistent"),
    ),
    TranslationTestCase(
        name="automation_condition",
        attributes={"automation_condition": "{{ automation_condition.eager() }}"},
        assertion=lambda asset_spec: asset_spec.automation_condition is not None,
    ),
    TranslationTestCase(
        name="key",
        attributes={"key": "{{ spec.key.to_user_string() + '_suffix' }}"},
        assertion=lambda asset_spec: asset_spec.key.path[-1].endswith("_suffix"),
        key_modifier=lambda key: AssetKey(path=list(key.path[:-1]) + [f"{key.path[-1]}_suffix"]),
    ),
    TranslationTestCase(
        name="key_prefix",
        attributes={"key_prefix": "cool_prefix"},
        assertion=lambda asset_spec: asset_spec.key.has_prefix(["cool_prefix"]),
        key_modifier=lambda key: AssetKey(path=["cool_prefix"] + list(key.path)),
    ),
    TranslationTestCase(
        name="partitions_defs",
        attributes={"partitions_def": {"type": "static", "partition_keys": ["foo", "bar"]}},
        assertion=lambda asset_spec: isinstance(
            asset_spec.partitions_def, StaticPartitionsDefinition
        ),
    ),
]


class TestTranslation:
    """Pytest test class for testing translation of asset attributes. You can subclass
    this class and implement a test_translation function using the various fixtures in
    order to comprehensively test asset translation options for your component.
    """

    @pytest.fixture(params=test_cases, ids=[case.name for case in test_cases])
    def translation_test_case(self, request):
        return request.param

    @pytest.fixture
    def attributes(self, translation_test_case: TranslationTestCase):
        return translation_test_case.attributes

    @pytest.fixture
    def assertion(self, translation_test_case: TranslationTestCase):
        return translation_test_case.assertion

    @pytest.fixture
    def key_modifier(self, translation_test_case: TranslationTestCase):
        return translation_test_case.key_modifier


class TestTranslationBatched(TestTranslation):
    """This version of the TestTranslation class is used to test the translation of
    asset attributes, applying all customizations in parallel to speed up tests for
    components which might be expensive to construct.
    """

    @pytest.fixture()
    def translation_test_case(self, request):
        deep_merge_all_attributes = {}
        for case in test_cases:
            deep_merge_all_attributes = deep_merge_dicts(deep_merge_all_attributes, case.attributes)
        merged_assertion = lambda asset_spec: all(case.assertion(asset_spec) for case in test_cases)

        # successively apply key modifiers
        def _merged_key_modifier(key):
            for case in test_cases:
                if case.key_modifier:
                    key = case.key_modifier(key)
            return key

        return TranslationTestCase(
            name="merged",
            attributes=deep_merge_all_attributes,
            assertion=merged_assertion,
            key_modifier=_merged_key_modifier,
        )


class TestOpCustomization:
    """Pytest test class for testing customization of op spec. You can subclass
    this class and implement a test_op_customization function using the various fixtures in
    order to comprehensively test op spec customization options for your component.
    """

    @pytest.fixture(
        params=[
            (
                {"name": "my_op"},
                lambda op: op.name == "my_op",
            ),
            (
                {"tags": {"foo": "bar"}},
                lambda op: op.tags.get("foo") == "bar",
            ),
            (
                {"backfill_policy": {"type": "single_run"}},
                lambda op: op.backfill_policy.max_partitions_per_run is None,
            ),
        ],
        ids=["name", "tags", "backfill_policy"],
    )
    def translation_test_case(self, request):
        return request.param

    @pytest.fixture
    def attributes(self, translation_test_case):
        return translation_test_case[0]

    @pytest.fixture
    def assertion(self, translation_test_case):
        return translation_test_case[1]

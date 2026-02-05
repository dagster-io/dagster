"""Tests for YAML template generation from Resolvable classes.

This test suite validates the YAML template generator's ability to handle
all patterns of classes inheriting from Resolvable, starting simple and
building up to complex union types and advanced patterns.
"""

import datetime
from typing import Annotated, Any, Literal, Optional, Union

import dagster as dg
import yaml
from dagster.components.resolved.core_models import (
    DailyPartitionsDefinitionModel,
    HourlyPartitionsDefinitionModel,
    StaticPartitionsDefinitionModel,
)
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)


def custom_resolver(context: dg.ResolutionContext, value: str) -> str:
    """Test resolver that converts to uppercase."""
    return value.upper()


def resolve_timestamp(context: dg.ResolutionContext, raw_timestamp: str) -> datetime.datetime:
    """Test resolver for datetime fields."""
    return datetime.datetime.fromisoformat(context.resolve_value(raw_timestamp, as_type=str))


class TestResolvableYamlTemplates:
    """Comprehensive test suite for Resolvable class YAML template generation."""

    def _test_schema_and_examples_for_model(
        self, model_class, expected_schema_contains=None, expected_example_contains=None
    ):
        """Helper to test both schema and example generation for a Resolvable model."""
        schema = model_class.model().model_json_schema()
        component_type = f"{model_class.__module__}.{model_class.__name__}"

        # Test schema generation
        schema_result = generate_defs_yaml_schema(component_type, schema)

        # Test example generation
        example_result = generate_defs_yaml_example_values(component_type, schema)

        # Schema output is a template with comments, not valid YAML
        # Only example output should be valid YAML
        parsed_example = yaml.safe_load(example_result)
        assert parsed_example is not None

        # Check component type is set correctly
        assert f"type: {component_type}" in schema_result
        assert f'type: "{component_type}"' in example_result

        # Check for expected content if provided
        if expected_schema_contains:
            for content in expected_schema_contains:
                assert content in schema_result, f"Expected '{content}' in schema output"

        if expected_example_contains:
            for content in expected_example_contains:
                assert content in example_result, f"Expected '{content}' in example output"

        return schema_result, example_result

    # Level 1: Basic Single Field Tests

    def test_single_string_field(self):
        """Test simplest possible Resolvable model."""

        class SimpleStringModel(dg.Resolvable, dg.Model):
            name: str

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            SimpleStringModel,
            expected_schema_contains=["name: <string>  # Required:"],
            expected_example_contains=['name: "example_string"'],
        )

    def test_basic_primitive_types(self):
        """Test all basic field types."""

        class BasicTypesModel(dg.Resolvable, dg.Model):
            name: str
            count: int
            price: float
            enabled: bool

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            BasicTypesModel,
            expected_schema_contains=[
                "name: <string>  # Required:",
                "count: <one of: integer, string>  # Required:",
                "price: <one of: number, string>  # Required:",
                "enabled: <one of: boolean, string>  # Required:",
            ],
            expected_example_contains=[
                'name: "example_string"',
                "count: 1",
                "price: 1.0",
                "enabled: true",
            ],
        )

    def test_optional_vs_required(self):
        """Test required/optional field detection."""

        class OptionalFieldsModel(dg.Resolvable, dg.Model):
            name: str  # Required
            description: Optional[str] = None  # Optional

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            OptionalFieldsModel,
            expected_schema_contains=[
                "name: <string>  # Required:",
                "description: <string>  # Optional:",
            ],
            expected_example_contains=[
                'name: "example_string"',
                'description: "example_string"',  # Shows up because Union includes string
            ],
        )

    # Level 2: Collections and Basic Structures

    def test_simple_collections(self):
        """Test list and dict handling."""

        class SimpleListModel(dg.Resolvable, dg.Model):
            names: list[str]
            numbers: list[int]
            metadata: dict[str, str]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            SimpleListModel,
            expected_schema_contains=[
                "names: <one of: array of string, string>  # Required:",
                "numbers: <one of: array of integer, string>  # Required:",
                "metadata: <one of: object, string>  # Required:",
            ],
            expected_example_contains=[
                'names:\n    - "example_string"',
                'numbers:\n    - "1"',
                'metadata:\n    key: "value"',
            ],
        )

    def test_nested_objects(self):
        """Test object expansion."""

        class ConfigModel(dg.Resolvable, dg.Model):
            timeout: int
            retries: int = 3

        class ParentModel(dg.Resolvable, dg.Model):
            name: str
            config: ConfigModel

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            ParentModel,
            expected_schema_contains=[
                "name: <string>  # Required:",
                "config:  # Required:",
                "    timeout: <one of: integer, string>  # Required:",
                "    retries: <one of: integer, string>  # Optional:",
            ],
            expected_example_contains=[
                'name: "example_string"',
                "config:\n    timeout: 1\n    retries: 1",
            ],
        )

    # Level 3: Resolver and Injection Features

    def test_custom_resolvers(self):
        """Test resolver field type overrides."""

        class ResolverModel(dg.Resolvable, dg.Model):
            name: Annotated[str, dg.Resolver(custom_resolver)]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            ResolverModel, expected_schema_contains=["name: <string>  # Required:"]
        )

    def test_injected_fields(self):
        """Test template injection fields."""

        class InjectedModel(dg.Resolvable, dg.Model):
            name: str
            template_value: dg.Injected[str]  # String that can be templated

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            InjectedModel,
            expected_schema_contains=[
                "name: <string>  # Required:",
                "template_value: <string>  # Required:",
            ],
        )

    def test_resolver_with_type_override(self):
        """Test resolver changes field type in schema."""

        class TypeOverrideModel(dg.Resolvable, dg.Model):
            timestamp: Annotated[
                datetime.datetime, dg.Resolver(resolve_timestamp, model_field_type=str)
            ]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            TypeOverrideModel,
            expected_schema_contains=["timestamp: <string>  # Required:"],
            expected_example_contains=['timestamp: "example_string"'],
        )

    # Level 4: Union Types (Core Focus)

    def test_simple_union_types(self):
        """Test basic Union[str, int] patterns."""

        class SimpleUnionModel(dg.Resolvable, dg.Model):
            value: Union[str, int]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            SimpleUnionModel,
            expected_schema_contains=["value: <one of: string, integer>  # Required:"],
            expected_example_contains=["value: 1"],  # Picks integer (non-string takes priority)
        )

    def test_union_with_resolvables(self):
        """Test Union with multiple Resolvable classes - core feature!"""

        class OptionA(dg.Resolvable, dg.Model):
            type: Literal["a"] = "a"
            field_a: str

        class OptionB(dg.Resolvable, dg.Model):
            type: Literal["b"] = "b"
            field_b: int

        class UnionResolvableModel(dg.Resolvable, dg.Model):
            choice: Union[OptionA, OptionB]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            UnionResolvableModel,
            expected_schema_contains=[
                "choice:  # Required:",
                "# Choose one of the following types:",
                "# Option 1 - OptionAModel:",
                "# type: <one of: string, string>  # Optional:",
                "# field_a: <string>  # Optional:",
                "# Option 2 - OptionBModel:",
                "# type: <one of: string, string>  # Optional:",
                "# field_b: <one of: integer, string>  # Optional:",
            ],
        )

    def test_complex_partition_union(self):
        """Test real partition definition union type."""

        class ComplexUnionModel(dg.Resolvable, dg.Model):
            partitions_def: Optional[
                Union[
                    HourlyPartitionsDefinitionModel,
                    DailyPartitionsDefinitionModel,
                    StaticPartitionsDefinitionModel,
                ]
            ] = None

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            ComplexUnionModel,
            expected_schema_contains=[
                "partitions_def:  # Optional:",
                "# Choose one of the following types:",
                "# Option 1 - HourlyPartitionsDefinitionModelModel:",
                "# start_date: <string>  # Optional:",
                "# Option 2 - DailyPartitionsDefinitionModelModel:",
                "# Option 3 - StaticPartitionsDefinitionModelModel:",
                "# partition_keys:",
            ],
        )

    # Level 5: Advanced Patterns

    def test_list_of_unions(self):
        """Test arrays with union type items."""

        class OptionA(dg.Resolvable, dg.Model):
            type: Literal["a"] = "a"
            value: str

        class OptionB(dg.Resolvable, dg.Model):
            type: Literal["b"] = "b"
            value: int

        class ListOfUnionsModel(dg.Resolvable, dg.Model):
            items: list[Union[OptionA, OptionB]]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            ListOfUnionsModel,
            expected_schema_contains=[
                "items:  # Required:",
                "- # Array of",  # Should expand array structure
            ],
        )

    def test_nested_resolvers(self):
        """Test nested resolvers within collections."""

        class NestedResolverModel(dg.Resolvable, dg.Model):
            values: Annotated[
                list[str], dg.Resolver.default(description="List of processed values")
            ]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            NestedResolverModel,
            expected_schema_contains=[
                "values: <one of: array of string, string>  # Required: List of processed values"
            ],
        )

    def test_real_world_complex_model(self):
        """Test mix of custom resolvers, unions, collections, and defaults."""

        class RealWorldModel(dg.Resolvable, dg.Model):
            name: str
            deps: Optional[list[str]] = None
            partitions_def: Optional[
                Union[
                    HourlyPartitionsDefinitionModel,
                    StaticPartitionsDefinitionModel,
                ]
            ] = None
            metadata: dict[str, Any] = {}

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            RealWorldModel,
            expected_schema_contains=[
                "name: <string>  # Required:",
                "deps: <one of: array of string, string>  # Optional:",
                "partitions_def:  # Optional:",
                "# Choose one of the following types:",
                "metadata: <one of: object, string>  # Optional:",
            ],
            expected_example_contains=['name: "example_string"', 'metadata:\n    key: "value"'],
        )

    # Level 6: Edge Cases and Error Conditions

    def test_empty_model(self):
        """Test component without properties."""

        class EmptyModel(dg.Resolvable, dg.Model):
            pass

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            EmptyModel,
            expected_schema_contains=["attributes:  # Optional: Attributes details"],
            expected_example_contains=["attributes: {}"],
        )

    def test_model_with_defaults(self):
        """Test models with various default values."""

        class DefaultsModel(dg.Resolvable, dg.Model):
            name: str
            count: int = 42
            enabled: bool = True
            description: Optional[str] = None
            tags: list[str] = []
            metadata: dict[str, str] = {}

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            DefaultsModel,
            expected_schema_contains=[
                "name: <string>  # Required:",
                "count: <one of: integer, string>  # Optional:",
                "enabled: <one of: boolean, string>  # Optional:",
                "description: <string>  # Optional:",
                "tags: <one of: array of string, string>  # Optional:",
                "metadata: <one of: object, string>  # Optional:",
            ],
            expected_example_contains=[
                'name: "example_string"',
                "count: 1",
                "enabled: true",
                'tags:\n    - "example_string"',
                'metadata:\n    key: "value"',
            ],
        )

    def test_deeply_nested_structure(self):
        """Test deeply nested object structures."""

        class Level3(dg.Resolvable, dg.Model):
            value: str

        class Level2(dg.Resolvable, dg.Model):
            level3: Level3

        class Level1(dg.Resolvable, dg.Model):
            level2: Level2

        class DeepModel(dg.Resolvable, dg.Model):
            level1: Level1

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            DeepModel,
            expected_schema_contains=[
                "level1:  # Required:",
                "  level2:  # Required:",
                "    level3:  # Required:",
                "      value: <string>  # Required:",
            ],
            expected_example_contains=[
                'level1:\n    level2:\n      level3:\n        value: "example_string"'
            ],
        )

    def test_union_with_optional_fields(self):
        """Test union types where options have optional fields."""

        class ConfigA(dg.Resolvable, dg.Model):
            type: Literal["config_a"] = "config_a"
            host: str
            port: int = 80

        class ConfigB(dg.Resolvable, dg.Model):
            type: Literal["config_b"] = "config_b"
            path: str
            timeout: Optional[int] = None

        class UnionOptionalModel(dg.Resolvable, dg.Model):
            config: Union[ConfigA, ConfigB]

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            UnionOptionalModel,
            expected_schema_contains=[
                "config:  # Required:",
                "# Choose one of the following types:",
                "# Option 1 - ConfigAModel:",
                "# host: <string>  # Optional:",
                "# port: <one of: integer, string>  # Optional:",
                "# Option 2 - ConfigBModel:",
                "# path: <string>  # Optional:",
                "# timeout: <one of: integer, string>  # Optional:",
            ],
        )

    def test_union_with_complex_nested_types(self):
        """Test union types with deeply nested complex structures."""

        class DatabaseConfig(dg.Resolvable, dg.Model):
            host: str
            port: int
            credentials: dict[str, str]
            ssl_config: dict[str, Any] = {}

        class S3Config(dg.Resolvable, dg.Model):
            bucket: str
            region: str
            access_keys: list[str]
            encryption: Optional[dict[str, str]] = None

        class FileSystemConfig(dg.Resolvable, dg.Model):
            base_path: str
            permissions: dict[str, int] = {}
            mount_options: list[str] = []

        class StorageBackend(dg.Resolvable, dg.Model):
            type: Literal["storage"] = "storage"
            config: Union[DatabaseConfig, S3Config, FileSystemConfig]
            retry_policy: dict[str, Any] = {"max_retries": 3}
            monitoring: Optional[list[str]] = None

        class CacheBackend(dg.Resolvable, dg.Model):
            type: Literal["cache"] = "cache"
            redis_config: dict[str, str]
            ttl_seconds: int = 3600
            cluster_nodes: list[dict[str, Any]] = []

        class ComplexNestedUnionModel(dg.Resolvable, dg.Model):
            name: str
            primary_backend: Union[StorageBackend, CacheBackend]
            fallback_backends: Optional[list[Union[StorageBackend, CacheBackend]]] = None
            global_config: dict[str, Any] = {}

        _schema_result, _example_result = self._test_schema_and_examples_for_model(
            ComplexNestedUnionModel,
            expected_schema_contains=[
                # Test top-level union type
                "primary_backend:  # Required:",
                "# Choose one of the following types:",
                "# Option 1 - StorageBackendModel:",
                "# Option 2 - CacheBackendModel:",
                # Test nested union type within StorageBackendModel.config
                "# config:  # Optional:",
                "      # Choose one of the following types:",
                "      # Option 1 - DatabaseConfigModel:",
                "      # Option 2 - S3ConfigModel:",
                "      # Option 3 - FileSystemConfigModel:",
                # Test array of union types
                "fallback_backends:  # Optional:",
                "- # Array of StorageBackendModel objects:",
                "  config:  # Required:",
                "    # Choose one of the following types:",
            ],
            expected_example_contains=[
                'name: "example_string"',
            ],
        )

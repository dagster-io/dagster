"""Tests for automatic template resolution of Config/ConfigurableResource in YAML components."""

from dataclasses import dataclass

import dagster as dg


class MyDatabaseConfig(dg.Config):
    database: str
    schema_: str = "main"


class MyResource(dg.ConfigurableResource):
    host: str
    port: int = 5432
    password: str = ""


class MyNestedResource(dg.ConfigurableResource):
    inner: MyResource
    label: str


def test_config_field_env_resolution(monkeypatch):
    """Config subclass fields should resolve {{ env('X') }} templates."""
    monkeypatch.setenv("TEST_DB_PATH", "/tmp/test.db")

    @dataclass
    class MyComponent(dg.Resolvable):
        db: MyDatabaseConfig

    result = MyComponent.resolve_from_yaml(
        """
db:
  database: "{{ env('TEST_DB_PATH') }}"
  schema_: analytics
"""
    )
    assert result.db.database == "/tmp/test.db"
    assert result.db.schema_ == "analytics"


def test_configurable_resource_field_env_resolution(monkeypatch):
    """ConfigurableResource subclass fields should resolve {{ env('X') }} templates."""
    monkeypatch.setenv("TEST_DB_HOST", "prod.db.example.com")

    @dataclass
    class MyComponent(dg.Resolvable):
        resource: MyResource

    result = MyComponent.resolve_from_yaml(
        """
resource:
  host: "{{ env('TEST_DB_HOST') }}"
  port: 9999
"""
    )
    assert result.resource.host == "prod.db.example.com"
    assert result.resource.port == 9999


def test_config_field_defaults_preserved(monkeypatch):
    """Unset fields on Config should use their defaults."""
    monkeypatch.setenv("TEST_HOST", "db.local")

    @dataclass
    class MyComponent(dg.Resolvable):
        resource: MyResource

    result = MyComponent.resolve_from_yaml(
        """
resource:
  host: "{{ env('TEST_HOST') }}"
"""
    )
    assert result.resource.host == "db.local"
    assert result.resource.port == 5432  # default
    assert result.resource.password == ""  # default


def test_optional_config_field(monkeypatch):
    """Optional Config field should resolve when present and be None when absent."""
    monkeypatch.setenv("TEST_HOST", "db.local")

    @dataclass
    class MyComponent(dg.Resolvable):
        resource: MyResource | None = None

    with_resource = MyComponent.resolve_from_yaml(
        """
resource:
  host: "{{ env('TEST_HOST') }}"
"""
    )
    assert with_resource.resource is not None
    assert with_resource.resource.host == "db.local"

    without_resource = MyComponent.resolve_from_yaml("{}")
    assert without_resource.resource is None


def test_list_of_config_fields(monkeypatch):
    """List of Config subclasses should have each element resolved."""
    monkeypatch.setenv("HOST_A", "host-a.local")
    monkeypatch.setenv("HOST_B", "host-b.local")

    @dataclass
    class MyComponent(dg.Resolvable):
        resources: list[MyResource]

    result = MyComponent.resolve_from_yaml(
        """
resources:
  - host: "{{ env('HOST_A') }}"
    port: 5432
  - host: "{{ env('HOST_B') }}"
    port: 6543
"""
    )
    assert len(result.resources) == 2
    assert result.resources[0].host == "host-a.local"
    assert result.resources[1].host == "host-b.local"
    assert result.resources[1].port == 6543


def test_numeric_field_via_env_template(monkeypatch):
    """Numeric fields should accept env var templates that resolve to the correct type."""
    monkeypatch.setenv("TEST_PORT", "8080")

    @dataclass
    class MyComponent(dg.Resolvable):
        resource: MyResource

    result = MyComponent.resolve_from_yaml(
        """
resource:
  host: localhost
  port: "{{ env('TEST_PORT') }}"
"""
    )
    assert result.resource.port == 8080
    assert isinstance(result.resource.port, int)


def test_config_alongside_other_resolvable_fields(monkeypatch):
    """Config field works correctly alongside plain Resolvable fields."""
    monkeypatch.setenv("COMPONENT_NAME", "my_component")
    monkeypatch.setenv("DB_PATH", "/data/prod.db")

    @dataclass
    class MyComponent(dg.Resolvable):
        name: str
        db: MyDatabaseConfig

    result = MyComponent.resolve_from_yaml(
        """
name: "{{ env('COMPONENT_NAME') }}"
db:
  database: "{{ env('DB_PATH') }}"
"""
    )
    assert result.name == "my_component"
    assert result.db.database == "/data/prod.db"


def test_config_field_plain_values():
    """Config field should work with plain (non-template) values."""

    @dataclass
    class MyComponent(dg.Resolvable):
        db: MyDatabaseConfig

    result = MyComponent.resolve_from_yaml(
        """
db:
  database: /tmp/plain.db
  schema_: public
"""
    )
    assert result.db.database == "/tmp/plain.db"
    assert result.db.schema_ == "public"

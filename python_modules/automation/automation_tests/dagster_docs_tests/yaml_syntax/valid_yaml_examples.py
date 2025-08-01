"""Docstring fixtures with valid YAML code blocks."""

from dagster._annotations import public


@public
class ValidYAMLFixtures:
    """Fixtures for testing valid YAML syntax in docstrings."""

    @public
    def simple_yaml_config(self):
        """Example with simple YAML configuration.

        Examples:
            Basic YAML configuration:

            .. code-block:: yaml

                database:
                  host: localhost
                  port: 5432
                  name: mydb
        """
        pass

    @public
    def complex_yaml_structure(self):
        """Example with complex YAML structure.

        Examples:
            Complex YAML with nested structures:

            .. code-block:: yaml

                pipeline:
                  stages:
                    - name: extract
                      config:
                        source: database
                        query: SELECT * FROM users
                    - name: transform
                      config:
                        operations:
                          - type: filter
                            condition: age > 18
                          - type: aggregate
                            group_by: [city, country]
                    - name: load
                      config:
                        destination: warehouse
                        table: user_summary
        """
        pass

    @public
    def yaml_with_special_types(self):
        """Example with YAML special types and values.

        Examples:
            YAML with various data types:

            .. code-block:: yaml

                config:
                  string_value: "hello world"
                  integer_value: 42
                  float_value: 3.14159
                  boolean_value: true
                  null_value: null
                  list_value:
                    - item1
                    - item2
                    - item3
                  timestamp: 2023-01-15T10:30:00Z
        """
        pass

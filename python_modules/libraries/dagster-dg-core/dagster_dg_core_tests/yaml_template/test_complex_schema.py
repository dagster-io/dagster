import json

from dagster_dg_core.yaml_template.converter import YamlTemplate


class TestComplexDbtProjectSchema:
    def test_dbt_project_component_model_schema(self):
        """Test the complex DbtProjectComponentModel schema provided by user."""
        schema_string = """{
    "$defs": {
        "AssetSpecUpdateKwargsModel": {
            "additionalProperties": false,
            "properties": {
                "deps": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "The asset keys for the upstream assets that this asset depends on.",
                    "examples": [
                        [
                            "my_database/my_schema/upstream_table"
                        ]
                    ],
                    "title": "Deps"
                },
                "description": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Human-readable description of the asset.",
                    "examples": [
                        "Refined sales data"
                    ],
                    "title": "Description"
                },
                "metadata": {
                    "anyOf": [
                        {
                            "additionalProperties": true,
                            "type": "object"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": "__DAGSTER_UNSET_DEFAULT__",
                    "description": "Additional metadata for the asset.",
                    "title": "Metadata"
                },
                "group_name": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Used to organize assets into groups, defaults to 'default'.",
                    "examples": [
                        "staging"
                    ],
                    "title": "Group Name"
                },
                "skippable": {
                    "anyOf": [
                        {
                            "type": "boolean"
                        },
                        {
                            "type": "null"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": null,
                    "description": "Whether this asset can be omitted during materialization, causing downstream dependencies to skip.",
                    "title": "Skippable"
                },
                "code_version": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "A version representing the code that produced the asset. Increment this value when the code changes.",
                    "examples": [
                        "3"
                    ],
                    "title": "Code Version"
                },
                "owners": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": null,
                    "description": "A list of strings representing owners of the asset. Each string can be a user's email address, or a team name prefixed with `team:`, e.g. `team:finops`.",
                    "examples": [
                        [
                            "team:analytics",
                            "nelson@hooli.com"
                        ]
                    ],
                    "title": "Owners"
                },
                "tags": {
                    "anyOf": [
                        {
                            "additionalProperties": {
                                "type": "string"
                            },
                            "type": "object"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": "__DAGSTER_UNSET_DEFAULT__",
                    "description": "Tags for filtering and organizing.",
                    "examples": [
                        {
                            "team": "analytics",
                            "tier": "prod"
                        }
                    ],
                    "title": "Tags"
                },
                "kinds": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": "__DAGSTER_UNSET_DEFAULT__",
                    "description": "A list of strings representing the kinds of the asset. These will be made visible in the Dagster UI.",
                    "examples": [
                        [
                            "snowflake"
                        ]
                    ],
                    "title": "Kinds"
                },
                "automation_condition": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "The condition under which the asset will be automatically materialized.",
                    "title": "Automation Condition"
                },
                "partitions_def": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/HourlyPartitionsDefinitionModel"
                        },
                        {
                            "$ref": "#/$defs/DailyPartitionsDefinitionModel"
                        },
                        {
                            "$ref": "#/$defs/WeeklyPartitionsDefinitionModel"
                        },
                        {
                            "$ref": "#/$defs/TimeWindowPartitionsDefinitionModel"
                        },
                        {
                            "$ref": "#/$defs/StaticPartitionsDefinitionModel"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": null,
                    "description": "The partitions definition for the asset.",
                    "title": "Partitions Def"
                },
                "key": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Key"
                },
                "key_prefix": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Prefix the existing asset key with the provided value.",
                    "title": "Key Prefix"
                }
            },
            "title": "AssetSpecUpdateKwargsModel",
            "type": "object"
        },
        "DagsterDbtComponentsTranslatorSettingsModel": {
            "additionalProperties": false,
            "properties": {
                "enable_asset_checks": {
                    "anyOf": [
                        {
                            "type": "boolean"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": true,
                    "title": "Enable Asset Checks"
                },
                "enable_duplicate_source_asset_keys": {
                    "anyOf": [
                        {
                            "type": "boolean"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": false,
                    "title": "Enable Duplicate Source Asset Keys"
                },
                "enable_code_references": {
                    "anyOf": [
                        {
                            "type": "boolean"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": true,
                    "title": "Enable Code References"
                },
                "enable_dbt_selection_by_name": {
                    "anyOf": [
                        {
                            "type": "boolean"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": false,
                    "title": "Enable Dbt Selection By Name"
                },
                "enable_source_tests_as_checks": {
                    "anyOf": [
                        {
                            "type": "boolean"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": false,
                    "title": "Enable Source Tests As Checks"
                }
            },
            "title": "DagsterDbtComponentsTranslatorSettingsModel",
            "type": "object"
        },
        "DailyPartitionsDefinitionModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "daily",
                    "default": "daily",
                    "title": "Type",
                    "type": "string"
                },
                "start_date": {
                    "title": "Start Date",
                    "type": "string"
                },
                "end_date": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "End Date"
                },
                "timezone": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Timezone"
                },
                "minute_offset": {
                    "default": 0,
                    "title": "Minute Offset",
                    "type": "integer"
                },
                "hour_offset": {
                    "default": 0,
                    "title": "Hour Offset",
                    "type": "integer"
                }
            },
            "required": [
                "start_date"
            ],
            "title": "DailyPartitionsDefinitionModel",
            "type": "object"
        },
        "DbtProjectArgsModel": {
            "additionalProperties": false,
            "properties": {
                "project_dir": {
                    "title": "Project Dir",
                    "type": "string"
                },
                "target_path": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Target Path"
                },
                "profiles_dir": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Profiles Dir"
                },
                "profile": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Profile"
                },
                "target": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Target"
                },
                "packaged_project_dir": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Packaged Project Dir"
                },
                "state_path": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "State Path"
                }
            },
            "required": [
                "project_dir"
            ],
            "title": "DbtProjectArgsModel",
            "type": "object"
        },
        "HourlyPartitionsDefinitionModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "hourly",
                    "default": "hourly",
                    "title": "Type",
                    "type": "string"
                },
                "start_date": {
                    "title": "Start Date",
                    "type": "string"
                },
                "end_date": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "End Date"
                },
                "timezone": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Timezone"
                },
                "minute_offset": {
                    "default": 0,
                    "title": "Minute Offset",
                    "type": "integer"
                }
            },
            "required": [
                "start_date"
            ],
            "title": "HourlyPartitionsDefinitionModel",
            "type": "object"
        },
        "MultiRunBackfillPolicyModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "multi_run",
                    "default": "multi_run",
                    "title": "Type",
                    "type": "string"
                },
                "max_partitions_per_run": {
                    "default": 1,
                    "title": "Max Partitions Per Run",
                    "type": "integer"
                }
            },
            "title": "MultiRunBackfillPolicyModel",
            "type": "object"
        },
        "OpSpecModel": {
            "additionalProperties": false,
            "properties": {
                "name": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Name"
                },
                "tags": {
                    "anyOf": [
                        {
                            "additionalProperties": true,
                            "type": "object"
                        },
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Tags"
                },
                "description": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Description"
                },
                "pool": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Pool"
                },
                "backfill_policy": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/SingleRunBackfillPolicyModel"
                        },
                        {
                            "$ref": "#/$defs/MultiRunBackfillPolicyModel"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "default": null,
                    "title": "Backfill Policy"
                }
            },
            "title": "OpSpecModel",
            "type": "object"
        },
        "SingleRunBackfillPolicyModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "single_run",
                    "default": "single_run",
                    "title": "Type",
                    "type": "string"
                }
            },
            "title": "SingleRunBackfillPolicyModel",
            "type": "object"
        },
        "StaticPartitionsDefinitionModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "static",
                    "default": "static",
                    "title": "Type",
                    "type": "string"
                },
                "partition_keys": {
                    "items": {
                        "type": "string"
                    },
                    "title": "Partition Keys",
                    "type": "array"
                }
            },
            "required": [
                "partition_keys"
            ],
            "title": "StaticPartitionsDefinitionModel",
            "type": "object"
        },
        "TimeWindowPartitionsDefinitionModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "time_window",
                    "default": "time_window",
                    "title": "Type",
                    "type": "string"
                },
                "start_date": {
                    "title": "Start Date",
                    "type": "string"
                },
                "end_date": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "End Date"
                },
                "timezone": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Timezone"
                },
                "fmt": {
                    "title": "Fmt",
                    "type": "string"
                },
                "cron_schedule": {
                    "title": "Cron Schedule",
                    "type": "string"
                }
            },
            "required": [
                "start_date",
                "fmt",
                "cron_schedule"
            ],
            "title": "TimeWindowPartitionsDefinitionModel",
            "type": "object"
        },
        "WeeklyPartitionsDefinitionModel": {
            "additionalProperties": false,
            "properties": {
                "type": {
                    "const": "weekly",
                    "default": "weekly",
                    "title": "Type",
                    "type": "string"
                },
                "start_date": {
                    "title": "Start Date",
                    "type": "string"
                },
                "end_date": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "End Date"
                },
                "timezone": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Timezone"
                },
                "minute_offset": {
                    "default": 0,
                    "title": "Minute Offset",
                    "type": "integer"
                },
                "hour_offset": {
                    "default": 0,
                    "title": "Hour Offset",
                    "type": "integer"
                },
                "day_offset": {
                    "default": 0,
                    "title": "Day Offset",
                    "type": "integer"
                }
            },
            "required": [
                "start_date"
            ],
            "title": "WeeklyPartitionsDefinitionModel",
            "type": "object"
        }
    },
    "additionalProperties": false,
    "properties": {
        "project": {
            "anyOf": [
                {
                    "type": "string"
                },
                {
                    "$ref": "#/$defs/DbtProjectArgsModel"
                }
            ],
            "description": "The path to the dbt project or a mapping defining a DbtProject",
            "examples": [
                "{{ project_root }}/path/to/dbt_project",
                {
                    "profile": "your_profile",
                    "project_dir": "path/to/dbt_project",
                    "target": "your_target"
                }
            ],
            "title": "Project"
        },
        "op": {
            "anyOf": [
                {
                    "$ref": "#/$defs/OpSpecModel"
                },
                {
                    "type": "string"
                },
                {
                    "type": "null"
                }
            ],
            "default": null,
            "description": "Op related arguments to set on the generated @dbt_assets",
            "examples": [
                {
                    "backfill_policy": {
                        "type": "single_run"
                    },
                    "name": "some_op",
                    "tags": {
                        "tag1": "value"
                    }
                }
            ],
            "title": "Op"
        },
        "translation": {
            "anyOf": [
                {
                    "type": "string"
                },
                {
                    "$ref": "#/$defs/AssetSpecUpdateKwargsModel"
                }
            ],
            "default": null,
            "title": "Translation"
        },
        "select": {
            "default": "fqn:*",
            "description": "The dbt selection string for models in the project you want to include.",
            "examples": [
                "tag:dagster"
            ],
            "title": "Select",
            "type": "string"
        },
        "exclude": {
            "default": "",
            "description": "The dbt selection string for models in the project you want to exclude.",
            "examples": [
                "tag:skip_dagster"
            ],
            "title": "Exclude",
            "type": "string"
        },
        "translation_settings": {
            "anyOf": [
                {
                    "$ref": "#/$defs/DagsterDbtComponentsTranslatorSettingsModel"
                },
                {
                    "type": "string"
                },
                {
                    "type": "null"
                }
            ],
            "default": null,
            "description": "Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
            "examples": [
                {
                    "enable_source_tests_as_checks": true
                }
            ],
            "title": "Translation Settings"
        },
        "prepare_if_dev": {
            "anyOf": [
                {
                    "type": "boolean"
                },
                {
                    "type": "string"
                }
            ],
            "default": true,
            "description": "Whether to prepare the dbt project every time in `dagster dev` or `dg` cli calls.",
            "title": "Prepare If Dev"
        }
    },
    "required": [
        "project"
    ],
    "title": "DbtProjectComponentModel",
    "type": "object"
}"""

        # Parse the JSON schema
        schema = json.loads(schema_string)

        # Generate YAML template
        template = YamlTemplate.from_json_schema(schema)
        result = template.to_string()

        # Verify the template was generated without errors
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify it contains the expected sections
        assert "# Template with instructions" in result
        assert "# EXAMPLE VALUES:" in result

        # Verify it contains some key properties
        assert "project:" in result  # Required field
        assert "Required" in result  # Should have required field comments
        assert "Optional" in result  # Should have optional field comments

        # Verify it handles complex nested structures
        assert "anyOf" not in result  # Should not leak schema internals
        assert "$ref" not in result  # Should not leak schema internals
        assert "$defs" not in result  # Should not leak schema internals

        # The template was generated without errors - we could print here if needed for manual inspection

        # The template should be reasonably sized (not empty, not excessively long)
        lines = result.split("\n")
        assert len(lines) > 10  # Should have substantial content
        assert len(lines) < 200  # But not be overwhelming

        # Verify some specific expected content
        assert "project: " in result
        assert '"example_string"' in result or '"' in result  # Should have example values

    def test_handles_unsupported_json_schema_features_gracefully(self):
        """Test that unsupported JSON Schema features are handled gracefully."""
        schema = {
            "type": "object",
            "properties": {
                "unsupported_feature": {"anyOf": [{"type": "string"}, {"type": "number"}]},
                "normal_property": {"type": "string"},
            },
        }

        template = YamlTemplate.from_json_schema(schema)
        result = template.to_string()

        # Should still generate a template, even if it can't handle all features perfectly
        assert "# Template with instructions" in result
        assert "normal_property:" in result
        assert "# EXAMPLE VALUES:" in result

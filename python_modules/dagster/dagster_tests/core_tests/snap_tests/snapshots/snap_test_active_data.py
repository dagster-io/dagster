# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_external_pipeline_data 1'] = '''{
  "__class__": "ExternalPipelineData",
  "active_presets": [
    {
      "__class__": "ExternalPresetData",
      "mode": "mode_one",
      "name": "kitchen_sink_preset",
      "run_config": {
        "foo": "bar"
      },
      "solid_selection": [
        "a_solid"
      ],
      "tags": {}
    },
    {
      "__class__": "ExternalPresetData",
      "mode": "default",
      "name": "plain_preset",
      "run_config": {},
      "solid_selection": null,
      "tags": {}
    }
  ],
  "name": "a_pipeline",
  "parent_pipeline_snapshot": null,
  "pipeline_snapshot": {
    "__class__": "PipelineSnapshot",
    "config_schema_snapshot": {
      "__class__": "ConfigSchemaSnapshot",
      "all_config_snaps_by_key": {
        "Any": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": null,
          "given_name": "Any",
          "key": "Any",
          "kind": {
            "__enum__": "ConfigTypeKind.ANY"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b": {
          "__class__": "ConfigTypeSnap",
          "description": "List of Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b",
          "enum_values": null,
          "fields": null,
          "given_name": null,
          "key": "Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b",
          "kind": {
            "__enum__": "ConfigTypeKind.ARRAY"
          },
          "scalar_kind": null,
          "type_param_keys": [
            "Shape.41de0e2d7b75524510155d0bdab8723c6feced3b"
          ]
        },
        "Bool": {
          "__class__": "ConfigTypeSnap",
          "description": "",
          "enum_values": null,
          "fields": null,
          "given_name": "Bool",
          "key": "Bool",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR"
          },
          "scalar_kind": {
            "__enum__": "ConfigScalarKind.BOOL"
          },
          "type_param_keys": null
        },
        "Float": {
          "__class__": "ConfigTypeSnap",
          "description": "",
          "enum_values": null,
          "fields": null,
          "given_name": "Float",
          "key": "Float",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR"
          },
          "scalar_kind": {
            "__enum__": "ConfigScalarKind.FLOAT"
          },
          "type_param_keys": null
        },
        "Int": {
          "__class__": "ConfigTypeSnap",
          "description": "",
          "enum_values": null,
          "fields": null,
          "given_name": "Int",
          "key": "Int",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR"
          },
          "scalar_kind": {
            "__enum__": "ConfigScalarKind.INT"
          },
          "type_param_keys": null
        },
        "ScalarUnion.Bool-Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": null,
          "given_name": null,
          "key": "ScalarUnion.Bool-Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR_UNION"
          },
          "scalar_kind": null,
          "type_param_keys": [
            "Bool",
            "Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59"
          ]
        },
        "ScalarUnion.Float-Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": null,
          "given_name": null,
          "key": "ScalarUnion.Float-Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR_UNION"
          },
          "scalar_kind": null,
          "type_param_keys": [
            "Float",
            "Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3"
          ]
        },
        "ScalarUnion.Int-Selector.a9799b971d12ace70a2d8803c883c863417d0725": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": null,
          "given_name": null,
          "key": "ScalarUnion.Int-Selector.a9799b971d12ace70a2d8803c883c863417d0725",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR_UNION"
          },
          "scalar_kind": null,
          "type_param_keys": [
            "Int",
            "Selector.a9799b971d12ace70a2d8803c883c863417d0725"
          ]
        },
        "ScalarUnion.String-Selector.e04723c9d9937e3ab21206435b22247cfbe58269": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": null,
          "given_name": null,
          "key": "ScalarUnion.String-Selector.e04723c9d9937e3ab21206435b22247cfbe58269",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR_UNION"
          },
          "scalar_kind": null,
          "type_param_keys": [
            "String",
            "Selector.e04723c9d9937e3ab21206435b22247cfbe58269"
          ]
        },
        "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "disabled",
              "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "enabled",
              "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
            }
          ],
          "given_name": null,
          "key": "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"config\\": {\\"retries\\": {\\"enabled\\": {}}}}",
              "description": null,
              "is_required": false,
              "name": "in_process",
              "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"config\\": {\\"max_concurrent\\": 0, \\"retries\\": {\\"enabled\\": {}}}}",
              "description": null,
              "is_required": false,
              "name": "multiprocess",
              "type_key": "Shape.fff3afcfe0467fefa4b97fb8f72911aeb0e8fe4e"
            }
          ],
          "given_name": null,
          "key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.a9799b971d12ace70a2d8803c883c863417d0725": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "json",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "pickle",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "value",
              "type_key": "Int"
            }
          ],
          "given_name": null,
          "key": "Selector.a9799b971d12ace70a2d8803c883c863417d0725",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "json",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "pickle",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "value",
              "type_key": "Bool"
            }
          ],
          "given_name": null,
          "key": "Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "json",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "pickle",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "value",
              "type_key": "Float"
            }
          ],
          "given_name": null,
          "key": "Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.e04723c9d9937e3ab21206435b22247cfbe58269": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "json",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "pickle",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "value",
              "type_key": "String"
            }
          ],
          "given_name": null,
          "key": "Selector.e04723c9d9937e3ab21206435b22247cfbe58269",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "json",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "pickle",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            }
          ],
          "given_name": null,
          "key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"config\\": {}}",
              "description": null,
              "is_required": false,
              "name": "filesystem",
              "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "in_memory",
              "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
            }
          ],
          "given_name": null,
          "key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "json",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "pickle",
              "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "value",
              "type_key": "Any"
            }
          ],
          "given_name": null,
          "key": "Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4",
          "kind": {
            "__enum__": "ConfigTypeKind.SELECTOR"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.241ac489ffa5f718db6444bae7849fb86a62e441": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "\\"INFO\\"",
              "description": null,
              "is_required": false,
              "name": "log_level",
              "type_key": "String"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "\\"dagster\\"",
              "description": null,
              "is_required": false,
              "name": "name",
              "type_key": "String"
            }
          ],
          "given_name": null,
          "key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.3baab16166bacfaf4705811e64d356112fd733cb": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"log_level\\": \\"INFO\\", \\"name\\": \\"dagster\\"}",
              "description": null,
              "is_required": false,
              "name": "config",
              "type_key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441"
            }
          ],
          "given_name": null,
          "key": "Shape.3baab16166bacfaf4705811e64d356112fd733cb",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.41de0e2d7b75524510155d0bdab8723c6feced3b": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "result",
              "type_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742"
            }
          ],
          "given_name": null,
          "key": "Shape.41de0e2d7b75524510155d0bdab8723c6feced3b",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": true,
              "name": "path",
              "type_key": "String"
            }
          ],
          "given_name": null,
          "key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.5a712cc73cd18a717376d6ed2fd442949644d5bb": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "a_solid",
              "type_key": "Shape.681fbe3d20630c62adc35f0362593dc0623c6cf2"
            }
          ],
          "given_name": null,
          "key": "Shape.5a712cc73cd18a717376d6ed2fd442949644d5bb",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.6811763b21837fa90300427f32281dcf8566e1b1": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "execution",
              "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "intermediate_storage",
              "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "loggers",
              "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "resources",
              "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"a_solid\\": {}}",
              "description": null,
              "is_required": false,
              "name": "solids",
              "type_key": "Shape.5a712cc73cd18a717376d6ed2fd442949644d5bb"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "storage",
              "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
            }
          ],
          "given_name": null,
          "key": "Shape.6811763b21837fa90300427f32281dcf8566e1b1",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.681fbe3d20630c62adc35f0362593dc0623c6cf2": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "outputs",
              "type_key": "Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b"
            }
          ],
          "given_name": null,
          "key": "Shape.681fbe3d20630c62adc35f0362593dc0623c6cf2",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{}",
              "description": null,
              "is_required": false,
              "name": "config",
              "type_key": "Shape.e26e0c525e2d2c66b5a06f4cfdd053de6d44e3ed"
            }
          ],
          "given_name": null,
          "key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.979b3d2fece4f3eb92e90f2ec9fb4c85efe9ea5c": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "marker_to_close",
              "type_key": "String"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"enabled\\": {}}",
              "description": null,
              "is_required": false,
              "name": "retries",
              "type_key": "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2"
            }
          ],
          "given_name": null,
          "key": "Shape.979b3d2fece4f3eb92e90f2ec9fb4c85efe9ea5c",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.a476f98f7c4e324d4b665af722d1f2cd7f99b023": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "0",
              "description": null,
              "is_required": false,
              "name": "max_concurrent",
              "type_key": "Int"
            },
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"enabled\\": {}}",
              "description": null,
              "is_required": false,
              "name": "retries",
              "type_key": "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2"
            }
          ],
          "given_name": null,
          "key": "Shape.a476f98f7c4e324d4b665af722d1f2cd7f99b023",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"retries\\": {\\"enabled\\": {}}}",
              "description": null,
              "is_required": false,
              "name": "config",
              "type_key": "Shape.979b3d2fece4f3eb92e90f2ec9fb4c85efe9ea5c"
            }
          ],
          "given_name": null,
          "key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [],
          "given_name": null,
          "key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.e26e0c525e2d2c66b5a06f4cfdd053de6d44e3ed": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "base_dir",
              "type_key": "String"
            }
          ],
          "given_name": null,
          "key": "Shape.e26e0c525e2d2c66b5a06f4cfdd053de6d44e3ed",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": false,
              "default_value_as_json_str": null,
              "description": null,
              "is_required": false,
              "name": "console",
              "type_key": "Shape.3baab16166bacfaf4705811e64d356112fd733cb"
            }
          ],
          "given_name": null,
          "key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "Shape.fff3afcfe0467fefa4b97fb8f72911aeb0e8fe4e": {
          "__class__": "ConfigTypeSnap",
          "description": null,
          "enum_values": null,
          "fields": [
            {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"max_concurrent\\": 0, \\"retries\\": {\\"enabled\\": {}}}",
              "description": null,
              "is_required": false,
              "name": "config",
              "type_key": "Shape.a476f98f7c4e324d4b665af722d1f2cd7f99b023"
            }
          ],
          "given_name": null,
          "key": "Shape.fff3afcfe0467fefa4b97fb8f72911aeb0e8fe4e",
          "kind": {
            "__enum__": "ConfigTypeKind.STRICT_SHAPE"
          },
          "scalar_kind": null,
          "type_param_keys": null
        },
        "String": {
          "__class__": "ConfigTypeSnap",
          "description": "",
          "enum_values": null,
          "fields": null,
          "given_name": "String",
          "key": "String",
          "kind": {
            "__enum__": "ConfigTypeKind.SCALAR"
          },
          "scalar_kind": {
            "__enum__": "ConfigScalarKind.STRING"
          },
          "type_param_keys": null
        }
      }
    },
    "dagster_type_namespace_snapshot": {
      "__class__": "DagsterTypeNamespaceSnapshot",
      "all_dagster_type_snaps_by_key": {
        "Any": {
          "__class__": "DagsterTypeSnap",
          "description": null,
          "display_name": "Any",
          "is_builtin": true,
          "key": "Any",
          "kind": {
            "__enum__": "DagsterTypeKind.ANY"
          },
          "loader_schema_key": "Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4",
          "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
          "name": "Any",
          "type_param_keys": []
        },
        "Bool": {
          "__class__": "DagsterTypeSnap",
          "description": null,
          "display_name": "Bool",
          "is_builtin": true,
          "key": "Bool",
          "kind": {
            "__enum__": "DagsterTypeKind.SCALAR"
          },
          "loader_schema_key": "ScalarUnion.Bool-Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59",
          "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
          "name": "Bool",
          "type_param_keys": []
        },
        "Float": {
          "__class__": "DagsterTypeSnap",
          "description": null,
          "display_name": "Float",
          "is_builtin": true,
          "key": "Float",
          "kind": {
            "__enum__": "DagsterTypeKind.SCALAR"
          },
          "loader_schema_key": "ScalarUnion.Float-Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3",
          "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
          "name": "Float",
          "type_param_keys": []
        },
        "Int": {
          "__class__": "DagsterTypeSnap",
          "description": null,
          "display_name": "Int",
          "is_builtin": true,
          "key": "Int",
          "kind": {
            "__enum__": "DagsterTypeKind.SCALAR"
          },
          "loader_schema_key": "ScalarUnion.Int-Selector.a9799b971d12ace70a2d8803c883c863417d0725",
          "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
          "name": "Int",
          "type_param_keys": []
        },
        "Nothing": {
          "__class__": "DagsterTypeSnap",
          "description": null,
          "display_name": "Nothing",
          "is_builtin": true,
          "key": "Nothing",
          "kind": {
            "__enum__": "DagsterTypeKind.NOTHING"
          },
          "loader_schema_key": null,
          "materializer_schema_key": null,
          "name": "Nothing",
          "type_param_keys": []
        },
        "String": {
          "__class__": "DagsterTypeSnap",
          "description": null,
          "display_name": "String",
          "is_builtin": true,
          "key": "String",
          "kind": {
            "__enum__": "DagsterTypeKind.SCALAR"
          },
          "loader_schema_key": "ScalarUnion.String-Selector.e04723c9d9937e3ab21206435b22247cfbe58269",
          "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
          "name": "String",
          "type_param_keys": []
        }
      }
    },
    "dep_structure_snapshot": {
      "__class__": "DependencyStructureSnapshot",
      "solid_invocation_snaps": [
        {
          "__class__": "SolidInvocationSnap",
          "input_dep_snaps": [],
          "solid_def_name": "a_solid",
          "solid_name": "a_solid",
          "tags": {}
        }
      ]
    },
    "description": null,
    "lineage_snapshot": null,
    "mode_def_snaps": [
      {
        "__class__": "ModeDefSnap",
        "description": null,
        "logger_def_snaps": [
          {
            "__class__": "LoggerDefSnap",
            "config_field_snap": {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"log_level\\": \\"INFO\\", \\"name\\": \\"dagster\\"}",
              "description": null,
              "is_required": false,
              "name": "config",
              "type_key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441"
            },
            "description": "The default colored console logger.",
            "name": "console"
          }
        ],
        "name": "default",
        "resource_def_snaps": [
          {
            "__class__": "ResourceDefSnap",
            "config_field_snap": null,
            "description": null,
            "name": "io_manager"
          }
        ],
        "root_config_key": "Shape.6811763b21837fa90300427f32281dcf8566e1b1"
      },
      {
        "__class__": "ModeDefSnap",
        "description": null,
        "logger_def_snaps": [
          {
            "__class__": "LoggerDefSnap",
            "config_field_snap": {
              "__class__": "ConfigFieldSnap",
              "default_provided": true,
              "default_value_as_json_str": "{\\"log_level\\": \\"INFO\\", \\"name\\": \\"dagster\\"}",
              "description": null,
              "is_required": false,
              "name": "config",
              "type_key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441"
            },
            "description": "The default colored console logger.",
            "name": "console"
          }
        ],
        "name": "mode_one",
        "resource_def_snaps": [
          {
            "__class__": "ResourceDefSnap",
            "config_field_snap": null,
            "description": null,
            "name": "io_manager"
          }
        ],
        "root_config_key": "Shape.6811763b21837fa90300427f32281dcf8566e1b1"
      }
    ],
    "name": "a_pipeline",
    "solid_definitions_snapshot": {
      "__class__": "SolidDefinitionsSnapshot",
      "composite_solid_def_snaps": [],
      "solid_def_snaps": [
        {
          "__class__": "SolidDefSnap",
          "config_field_snap": null,
          "description": null,
          "input_def_snaps": [],
          "name": "a_solid",
          "output_def_snaps": [
            {
              "__class__": "OutputDefSnap",
              "dagster_type_key": "Any",
              "description": null,
              "is_dynamic": false,
              "is_required": true,
              "name": "result"
            }
          ],
          "required_resource_keys": [],
          "tags": {}
        }
      ]
    },
    "tags": {}
  }
}'''

snapshots['test_external_repository_data 1'] = '''{
  "__class__": "ExternalRepositoryData",
  "external_executable_datas": [],
  "external_job_datas": [],
  "external_partition_set_datas": [
    {
      "__class__": "ExternalPartitionSetData",
      "mode": "default",
      "name": "a_schedule_partitions",
      "pipeline_name": "a_pipeline",
      "solid_selection": null
    }
  ],
  "external_pipeline_datas": [
    {
      "__class__": "ExternalPipelineData",
      "active_presets": [
        {
          "__class__": "ExternalPresetData",
          "mode": "mode_one",
          "name": "kitchen_sink_preset",
          "run_config": {
            "foo": "bar"
          },
          "solid_selection": [
            "a_solid"
          ],
          "tags": {}
        },
        {
          "__class__": "ExternalPresetData",
          "mode": "default",
          "name": "plain_preset",
          "run_config": {},
          "solid_selection": null,
          "tags": {}
        }
      ],
      "name": "a_pipeline",
      "parent_pipeline_snapshot": null,
      "pipeline_snapshot": {
        "__class__": "PipelineSnapshot",
        "config_schema_snapshot": {
          "__class__": "ConfigSchemaSnapshot",
          "all_config_snaps_by_key": {
            "Any": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": null,
              "given_name": "Any",
              "key": "Any",
              "kind": {
                "__enum__": "ConfigTypeKind.ANY"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b": {
              "__class__": "ConfigTypeSnap",
              "description": "List of Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b",
              "enum_values": null,
              "fields": null,
              "given_name": null,
              "key": "Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b",
              "kind": {
                "__enum__": "ConfigTypeKind.ARRAY"
              },
              "scalar_kind": null,
              "type_param_keys": [
                "Shape.41de0e2d7b75524510155d0bdab8723c6feced3b"
              ]
            },
            "Bool": {
              "__class__": "ConfigTypeSnap",
              "description": "",
              "enum_values": null,
              "fields": null,
              "given_name": "Bool",
              "key": "Bool",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR"
              },
              "scalar_kind": {
                "__enum__": "ConfigScalarKind.BOOL"
              },
              "type_param_keys": null
            },
            "Float": {
              "__class__": "ConfigTypeSnap",
              "description": "",
              "enum_values": null,
              "fields": null,
              "given_name": "Float",
              "key": "Float",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR"
              },
              "scalar_kind": {
                "__enum__": "ConfigScalarKind.FLOAT"
              },
              "type_param_keys": null
            },
            "Int": {
              "__class__": "ConfigTypeSnap",
              "description": "",
              "enum_values": null,
              "fields": null,
              "given_name": "Int",
              "key": "Int",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR"
              },
              "scalar_kind": {
                "__enum__": "ConfigScalarKind.INT"
              },
              "type_param_keys": null
            },
            "ScalarUnion.Bool-Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": null,
              "given_name": null,
              "key": "ScalarUnion.Bool-Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR_UNION"
              },
              "scalar_kind": null,
              "type_param_keys": [
                "Bool",
                "Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59"
              ]
            },
            "ScalarUnion.Float-Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": null,
              "given_name": null,
              "key": "ScalarUnion.Float-Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR_UNION"
              },
              "scalar_kind": null,
              "type_param_keys": [
                "Float",
                "Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3"
              ]
            },
            "ScalarUnion.Int-Selector.a9799b971d12ace70a2d8803c883c863417d0725": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": null,
              "given_name": null,
              "key": "ScalarUnion.Int-Selector.a9799b971d12ace70a2d8803c883c863417d0725",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR_UNION"
              },
              "scalar_kind": null,
              "type_param_keys": [
                "Int",
                "Selector.a9799b971d12ace70a2d8803c883c863417d0725"
              ]
            },
            "ScalarUnion.String-Selector.e04723c9d9937e3ab21206435b22247cfbe58269": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": null,
              "given_name": null,
              "key": "ScalarUnion.String-Selector.e04723c9d9937e3ab21206435b22247cfbe58269",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR_UNION"
              },
              "scalar_kind": null,
              "type_param_keys": [
                "String",
                "Selector.e04723c9d9937e3ab21206435b22247cfbe58269"
              ]
            },
            "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "disabled",
                  "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "enabled",
                  "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
                }
              ],
              "given_name": null,
              "key": "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"config\\": {\\"retries\\": {\\"enabled\\": {}}}}",
                  "description": null,
                  "is_required": false,
                  "name": "in_process",
                  "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"config\\": {\\"max_concurrent\\": 0, \\"retries\\": {\\"enabled\\": {}}}}",
                  "description": null,
                  "is_required": false,
                  "name": "multiprocess",
                  "type_key": "Shape.fff3afcfe0467fefa4b97fb8f72911aeb0e8fe4e"
                }
              ],
              "given_name": null,
              "key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.a9799b971d12ace70a2d8803c883c863417d0725": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "json",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "pickle",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "value",
                  "type_key": "Int"
                }
              ],
              "given_name": null,
              "key": "Selector.a9799b971d12ace70a2d8803c883c863417d0725",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "json",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "pickle",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "value",
                  "type_key": "Bool"
                }
              ],
              "given_name": null,
              "key": "Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "json",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "pickle",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "value",
                  "type_key": "Float"
                }
              ],
              "given_name": null,
              "key": "Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.e04723c9d9937e3ab21206435b22247cfbe58269": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "json",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "pickle",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "value",
                  "type_key": "String"
                }
              ],
              "given_name": null,
              "key": "Selector.e04723c9d9937e3ab21206435b22247cfbe58269",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "json",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "pickle",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                }
              ],
              "given_name": null,
              "key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"config\\": {}}",
                  "description": null,
                  "is_required": false,
                  "name": "filesystem",
                  "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "in_memory",
                  "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
                }
              ],
              "given_name": null,
              "key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "json",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "pickle",
                  "type_key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "value",
                  "type_key": "Any"
                }
              ],
              "given_name": null,
              "key": "Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4",
              "kind": {
                "__enum__": "ConfigTypeKind.SELECTOR"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.241ac489ffa5f718db6444bae7849fb86a62e441": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "\\"INFO\\"",
                  "description": null,
                  "is_required": false,
                  "name": "log_level",
                  "type_key": "String"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "\\"dagster\\"",
                  "description": null,
                  "is_required": false,
                  "name": "name",
                  "type_key": "String"
                }
              ],
              "given_name": null,
              "key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.3baab16166bacfaf4705811e64d356112fd733cb": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"log_level\\": \\"INFO\\", \\"name\\": \\"dagster\\"}",
                  "description": null,
                  "is_required": false,
                  "name": "config",
                  "type_key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441"
                }
              ],
              "given_name": null,
              "key": "Shape.3baab16166bacfaf4705811e64d356112fd733cb",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.41de0e2d7b75524510155d0bdab8723c6feced3b": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "result",
                  "type_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742"
                }
              ],
              "given_name": null,
              "key": "Shape.41de0e2d7b75524510155d0bdab8723c6feced3b",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": true,
                  "name": "path",
                  "type_key": "String"
                }
              ],
              "given_name": null,
              "key": "Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.5a712cc73cd18a717376d6ed2fd442949644d5bb": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "a_solid",
                  "type_key": "Shape.681fbe3d20630c62adc35f0362593dc0623c6cf2"
                }
              ],
              "given_name": null,
              "key": "Shape.5a712cc73cd18a717376d6ed2fd442949644d5bb",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.6811763b21837fa90300427f32281dcf8566e1b1": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "execution",
                  "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "intermediate_storage",
                  "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "loggers",
                  "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "resources",
                  "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"a_solid\\": {}}",
                  "description": null,
                  "is_required": false,
                  "name": "solids",
                  "type_key": "Shape.5a712cc73cd18a717376d6ed2fd442949644d5bb"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "storage",
                  "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
                }
              ],
              "given_name": null,
              "key": "Shape.6811763b21837fa90300427f32281dcf8566e1b1",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.681fbe3d20630c62adc35f0362593dc0623c6cf2": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "outputs",
                  "type_key": "Array.Shape.41de0e2d7b75524510155d0bdab8723c6feced3b"
                }
              ],
              "given_name": null,
              "key": "Shape.681fbe3d20630c62adc35f0362593dc0623c6cf2",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{}",
                  "description": null,
                  "is_required": false,
                  "name": "config",
                  "type_key": "Shape.e26e0c525e2d2c66b5a06f4cfdd053de6d44e3ed"
                }
              ],
              "given_name": null,
              "key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.979b3d2fece4f3eb92e90f2ec9fb4c85efe9ea5c": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "marker_to_close",
                  "type_key": "String"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"enabled\\": {}}",
                  "description": null,
                  "is_required": false,
                  "name": "retries",
                  "type_key": "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2"
                }
              ],
              "given_name": null,
              "key": "Shape.979b3d2fece4f3eb92e90f2ec9fb4c85efe9ea5c",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.a476f98f7c4e324d4b665af722d1f2cd7f99b023": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "0",
                  "description": null,
                  "is_required": false,
                  "name": "max_concurrent",
                  "type_key": "Int"
                },
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"enabled\\": {}}",
                  "description": null,
                  "is_required": false,
                  "name": "retries",
                  "type_key": "Selector.1bfb167aea90780aa679597800c71bd8c65ed0b2"
                }
              ],
              "given_name": null,
              "key": "Shape.a476f98f7c4e324d4b665af722d1f2cd7f99b023",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"retries\\": {\\"enabled\\": {}}}",
                  "description": null,
                  "is_required": false,
                  "name": "config",
                  "type_key": "Shape.979b3d2fece4f3eb92e90f2ec9fb4c85efe9ea5c"
                }
              ],
              "given_name": null,
              "key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [],
              "given_name": null,
              "key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.e26e0c525e2d2c66b5a06f4cfdd053de6d44e3ed": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "base_dir",
                  "type_key": "String"
                }
              ],
              "given_name": null,
              "key": "Shape.e26e0c525e2d2c66b5a06f4cfdd053de6d44e3ed",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": false,
                  "default_value_as_json_str": null,
                  "description": null,
                  "is_required": false,
                  "name": "console",
                  "type_key": "Shape.3baab16166bacfaf4705811e64d356112fd733cb"
                }
              ],
              "given_name": null,
              "key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "Shape.fff3afcfe0467fefa4b97fb8f72911aeb0e8fe4e": {
              "__class__": "ConfigTypeSnap",
              "description": null,
              "enum_values": null,
              "fields": [
                {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"max_concurrent\\": 0, \\"retries\\": {\\"enabled\\": {}}}",
                  "description": null,
                  "is_required": false,
                  "name": "config",
                  "type_key": "Shape.a476f98f7c4e324d4b665af722d1f2cd7f99b023"
                }
              ],
              "given_name": null,
              "key": "Shape.fff3afcfe0467fefa4b97fb8f72911aeb0e8fe4e",
              "kind": {
                "__enum__": "ConfigTypeKind.STRICT_SHAPE"
              },
              "scalar_kind": null,
              "type_param_keys": null
            },
            "String": {
              "__class__": "ConfigTypeSnap",
              "description": "",
              "enum_values": null,
              "fields": null,
              "given_name": "String",
              "key": "String",
              "kind": {
                "__enum__": "ConfigTypeKind.SCALAR"
              },
              "scalar_kind": {
                "__enum__": "ConfigScalarKind.STRING"
              },
              "type_param_keys": null
            }
          }
        },
        "dagster_type_namespace_snapshot": {
          "__class__": "DagsterTypeNamespaceSnapshot",
          "all_dagster_type_snaps_by_key": {
            "Any": {
              "__class__": "DagsterTypeSnap",
              "description": null,
              "display_name": "Any",
              "is_builtin": true,
              "key": "Any",
              "kind": {
                "__enum__": "DagsterTypeKind.ANY"
              },
              "loader_schema_key": "Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4",
              "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
              "name": "Any",
              "type_param_keys": []
            },
            "Bool": {
              "__class__": "DagsterTypeSnap",
              "description": null,
              "display_name": "Bool",
              "is_builtin": true,
              "key": "Bool",
              "kind": {
                "__enum__": "DagsterTypeKind.SCALAR"
              },
              "loader_schema_key": "ScalarUnion.Bool-Selector.be5d518b39e86a43c5f2eecaf538c1f6c7711b59",
              "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
              "name": "Bool",
              "type_param_keys": []
            },
            "Float": {
              "__class__": "DagsterTypeSnap",
              "description": null,
              "display_name": "Float",
              "is_builtin": true,
              "key": "Float",
              "kind": {
                "__enum__": "DagsterTypeKind.SCALAR"
              },
              "loader_schema_key": "ScalarUnion.Float-Selector.d00a37e3807d37c9f69cc62997c4a5f4a176e5c3",
              "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
              "name": "Float",
              "type_param_keys": []
            },
            "Int": {
              "__class__": "DagsterTypeSnap",
              "description": null,
              "display_name": "Int",
              "is_builtin": true,
              "key": "Int",
              "kind": {
                "__enum__": "DagsterTypeKind.SCALAR"
              },
              "loader_schema_key": "ScalarUnion.Int-Selector.a9799b971d12ace70a2d8803c883c863417d0725",
              "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
              "name": "Int",
              "type_param_keys": []
            },
            "Nothing": {
              "__class__": "DagsterTypeSnap",
              "description": null,
              "display_name": "Nothing",
              "is_builtin": true,
              "key": "Nothing",
              "kind": {
                "__enum__": "DagsterTypeKind.NOTHING"
              },
              "loader_schema_key": null,
              "materializer_schema_key": null,
              "name": "Nothing",
              "type_param_keys": []
            },
            "String": {
              "__class__": "DagsterTypeSnap",
              "description": null,
              "display_name": "String",
              "is_builtin": true,
              "key": "String",
              "kind": {
                "__enum__": "DagsterTypeKind.SCALAR"
              },
              "loader_schema_key": "ScalarUnion.String-Selector.e04723c9d9937e3ab21206435b22247cfbe58269",
              "materializer_schema_key": "Selector.e52fa3afbe531d9522fae1206f3ae9d248775742",
              "name": "String",
              "type_param_keys": []
            }
          }
        },
        "dep_structure_snapshot": {
          "__class__": "DependencyStructureSnapshot",
          "solid_invocation_snaps": [
            {
              "__class__": "SolidInvocationSnap",
              "input_dep_snaps": [],
              "solid_def_name": "a_solid",
              "solid_name": "a_solid",
              "tags": {}
            }
          ]
        },
        "description": null,
        "lineage_snapshot": null,
        "mode_def_snaps": [
          {
            "__class__": "ModeDefSnap",
            "description": null,
            "logger_def_snaps": [
              {
                "__class__": "LoggerDefSnap",
                "config_field_snap": {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"log_level\\": \\"INFO\\", \\"name\\": \\"dagster\\"}",
                  "description": null,
                  "is_required": false,
                  "name": "config",
                  "type_key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441"
                },
                "description": "The default colored console logger.",
                "name": "console"
              }
            ],
            "name": "default",
            "resource_def_snaps": [
              {
                "__class__": "ResourceDefSnap",
                "config_field_snap": null,
                "description": null,
                "name": "io_manager"
              }
            ],
            "root_config_key": "Shape.6811763b21837fa90300427f32281dcf8566e1b1"
          },
          {
            "__class__": "ModeDefSnap",
            "description": null,
            "logger_def_snaps": [
              {
                "__class__": "LoggerDefSnap",
                "config_field_snap": {
                  "__class__": "ConfigFieldSnap",
                  "default_provided": true,
                  "default_value_as_json_str": "{\\"log_level\\": \\"INFO\\", \\"name\\": \\"dagster\\"}",
                  "description": null,
                  "is_required": false,
                  "name": "config",
                  "type_key": "Shape.241ac489ffa5f718db6444bae7849fb86a62e441"
                },
                "description": "The default colored console logger.",
                "name": "console"
              }
            ],
            "name": "mode_one",
            "resource_def_snaps": [
              {
                "__class__": "ResourceDefSnap",
                "config_field_snap": null,
                "description": null,
                "name": "io_manager"
              }
            ],
            "root_config_key": "Shape.6811763b21837fa90300427f32281dcf8566e1b1"
          }
        ],
        "name": "a_pipeline",
        "solid_definitions_snapshot": {
          "__class__": "SolidDefinitionsSnapshot",
          "composite_solid_def_snaps": [],
          "solid_def_snaps": [
            {
              "__class__": "SolidDefSnap",
              "config_field_snap": null,
              "description": null,
              "input_def_snaps": [],
              "name": "a_solid",
              "output_def_snaps": [
                {
                  "__class__": "OutputDefSnap",
                  "dagster_type_key": "Any",
                  "description": null,
                  "is_dynamic": false,
                  "is_required": true,
                  "name": "result"
                }
              ],
              "required_resource_keys": [],
              "tags": {}
            }
          ]
        },
        "tags": {}
      }
    }
  ],
  "external_schedule_datas": [
    {
      "__class__": "ExternalScheduleData",
      "cron_schedule": "0 0 * * *",
      "environment_vars": {},
      "execution_timezone": "US/Central",
      "mode": "default",
      "name": "a_schedule",
      "partition_set_name": "a_schedule_partitions",
      "pipeline_name": "a_pipeline",
      "solid_selection": null
    }
  ],
  "external_sensor_datas": [],
  "name": "repo"
}'''

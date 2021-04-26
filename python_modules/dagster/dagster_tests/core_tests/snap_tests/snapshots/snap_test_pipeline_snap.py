# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_basic_dep_fan_out 1'] = '''{
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
      "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb": {
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
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb",
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
      "Shape.0bb49540f1708dcf5378009c9571eba999502e19": {
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
            "name": "io_manager",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
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
      "Shape.743e47901855cb245064dd633e217bfcb49a11a7": {
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
            "name": "config",
            "type_key": "Any"
          }
        ],
        "given_name": null,
        "key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7",
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
      "Shape.a3851e1e776312228af2d02b2ac81a7efa91cac6": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"in_process\\": {}}",
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
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
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
            "default_value_as_json_str": "{\\"io_manager\\": {}}",
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"passone\\": {}, \\"passtwo\\": {}, \\"return_one\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.edbb8443841c38bd5fdab49817129a99422175cc"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
          }
        ],
        "given_name": null,
        "key": "Shape.a3851e1e776312228af2d02b2ac81a7efa91cac6",
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
      "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727": {
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
            "name": "config",
            "type_key": "Any"
          },
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
        "key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727",
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
      "Shape.edbb8443841c38bd5fdab49817129a99422175cc": {
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
            "name": "passone",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "passtwo",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "return_one",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          }
        ],
        "given_name": null,
        "key": "Shape.edbb8443841c38bd5fdab49817129a99422175cc",
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
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "value",
            "is_dynamic_collect": false,
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "result",
                "solid_name": "return_one"
              }
            ]
          }
        ],
        "is_dynamic_mapped": false,
        "solid_def_name": "passthrough",
        "solid_name": "passone",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "value",
            "is_dynamic_collect": false,
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "result",
                "solid_name": "return_one"
              }
            ]
          }
        ],
        "is_dynamic_mapped": false,
        "solid_def_name": "passthrough",
        "solid_name": "passtwo",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [],
        "is_dynamic_mapped": false,
        "solid_def_name": "return_one",
        "solid_name": "return_one",
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
          "config_field_snap": {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "config",
            "type_key": "Any"
          },
          "description": null,
          "name": "io_manager"
        }
      ],
      "root_config_key": "Shape.a3851e1e776312228af2d02b2ac81a7efa91cac6"
    }
  ],
  "name": "single_dep_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [
          {
            "__class__": "InputDefSnap",
            "dagster_type_key": "Int",
            "description": null,
            "name": "value"
          }
        ],
        "name": "passthrough",
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
      },
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [],
        "name": "return_one",
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
}'''

snapshots['test_basic_dep_fan_out 2'] = '90a2f08212ad5b17025e6e1f2a12f28dfa5349d4'

snapshots['test_basic_fan_in 1'] = '''{
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
      "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb": {
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
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb",
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
      "Shape.0bb49540f1708dcf5378009c9571eba999502e19": {
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
            "name": "io_manager",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
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
      "Shape.4b879e06831d8ba90675c88d503afbc229425ade": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"in_process\\": {}}",
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
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
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
            "default_value_as_json_str": "{\\"io_manager\\": {}}",
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"nothing_one\\": {}, \\"nothing_two\\": {}, \\"take_nothings\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.62826049882b459c7302d9577e5848d385d58b62"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
          }
        ],
        "given_name": null,
        "key": "Shape.4b879e06831d8ba90675c88d503afbc229425ade",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "scalar_kind": null,
        "type_param_keys": null
      },
      "Shape.62826049882b459c7302d9577e5848d385d58b62": {
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
            "name": "nothing_one",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "nothing_two",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "take_nothings",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          }
        ],
        "given_name": null,
        "key": "Shape.62826049882b459c7302d9577e5848d385d58b62",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "scalar_kind": null,
        "type_param_keys": null
      },
      "Shape.743e47901855cb245064dd633e217bfcb49a11a7": {
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
            "name": "config",
            "type_key": "Any"
          }
        ],
        "given_name": null,
        "key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7",
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
      "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727": {
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
            "name": "config",
            "type_key": "Any"
          },
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
        "key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727",
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
        "is_dynamic_mapped": false,
        "solid_def_name": "return_nothing",
        "solid_name": "nothing_one",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [],
        "is_dynamic_mapped": false,
        "solid_def_name": "return_nothing",
        "solid_name": "nothing_two",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "nothing",
            "is_dynamic_collect": false,
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "result",
                "solid_name": "nothing_one"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "result",
                "solid_name": "nothing_two"
              }
            ]
          }
        ],
        "is_dynamic_mapped": false,
        "solid_def_name": "take_nothings",
        "solid_name": "take_nothings",
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
          "config_field_snap": {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "config",
            "type_key": "Any"
          },
          "description": null,
          "name": "io_manager"
        }
      ],
      "root_config_key": "Shape.4b879e06831d8ba90675c88d503afbc229425ade"
    }
  ],
  "name": "fan_in_test",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [],
        "name": "return_nothing",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_dynamic": false,
            "is_required": true,
            "name": "result"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      },
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [
          {
            "__class__": "InputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "nothing"
          }
        ],
        "name": "take_nothings",
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
}'''

snapshots['test_basic_fan_in 2'] = '1a2dbcc9bcbe0db8ac41eeba0f73b0899207fd46'

snapshots['test_deserialize_solid_def_snaps_multi_type_config 1'] = '''{
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
      "name": "bar",
      "type_key": "Selector.c12ab659793f168246640a294e913ac9d90a242a"
    },
    {
      "__class__": "ConfigFieldSnap",
      "default_provided": false,
      "default_value_as_json_str": null,
      "description": null,
      "is_required": true,
      "name": "foo",
      "type_key": "Array.Float"
    }
  ],
  "given_name": null,
  "key": "Permissive.bda2965be6725b48329d76783336ed442951fd54",
  "kind": {
    "__enum__": "ConfigTypeKind.PERMISSIVE_SHAPE"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_empty_pipeline_snap_props 1'] = '''{
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
      "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb": {
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
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb",
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
      "Shape.0bb49540f1708dcf5378009c9571eba999502e19": {
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
            "name": "io_manager",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
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
      "Shape.448bc7596c94071a7de00341f685ece16b2126cb": {
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
            "name": "noop_solid",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          }
        ],
        "given_name": null,
        "key": "Shape.448bc7596c94071a7de00341f685ece16b2126cb",
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
      "Shape.743e47901855cb245064dd633e217bfcb49a11a7": {
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
            "name": "config",
            "type_key": "Any"
          }
        ],
        "given_name": null,
        "key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7",
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
      "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727": {
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
            "name": "config",
            "type_key": "Any"
          },
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
        "key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727",
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
      "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"in_process\\": {}}",
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
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
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
            "default_value_as_json_str": "{\\"io_manager\\": {}}",
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"noop_solid\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.448bc7596c94071a7de00341f685ece16b2126cb"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
          }
        ],
        "given_name": null,
        "key": "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71",
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
        "is_dynamic_mapped": false,
        "solid_def_name": "noop_solid",
        "solid_name": "noop_solid",
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
          "config_field_snap": {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "config",
            "type_key": "Any"
          },
          "description": null,
          "name": "io_manager"
        }
      ],
      "root_config_key": "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71"
    }
  ],
  "name": "noop_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
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
}'''

snapshots['test_empty_pipeline_snap_props 2'] = '966a50e2092e6915a4434006c6edf4aafd2aea0a'

snapshots['test_empty_pipeline_snap_snapshot 1'] = '''{
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
      "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb": {
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
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb",
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
      "Shape.0bb49540f1708dcf5378009c9571eba999502e19": {
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
            "name": "io_manager",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
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
      "Shape.448bc7596c94071a7de00341f685ece16b2126cb": {
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
            "name": "noop_solid",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          }
        ],
        "given_name": null,
        "key": "Shape.448bc7596c94071a7de00341f685ece16b2126cb",
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
      "Shape.743e47901855cb245064dd633e217bfcb49a11a7": {
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
            "name": "config",
            "type_key": "Any"
          }
        ],
        "given_name": null,
        "key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7",
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
      "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727": {
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
            "name": "config",
            "type_key": "Any"
          },
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
        "key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727",
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
      "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"in_process\\": {}}",
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
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
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
            "default_value_as_json_str": "{\\"io_manager\\": {}}",
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"noop_solid\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.448bc7596c94071a7de00341f685ece16b2126cb"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
          }
        ],
        "given_name": null,
        "key": "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71",
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
        "is_dynamic_mapped": false,
        "solid_def_name": "noop_solid",
        "solid_name": "noop_solid",
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
          "config_field_snap": {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "config",
            "type_key": "Any"
          },
          "description": null,
          "name": "io_manager"
        }
      ],
      "root_config_key": "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71"
    }
  ],
  "name": "noop_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
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
}'''

snapshots['test_multi_type_config_array_dict_fields[Permissive] 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "List of Array.Permissive.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "enum_values": null,
  "fields": null,
  "given_name": null,
  "key": "Array.Permissive.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "kind": {
    "__enum__": "ConfigTypeKind.ARRAY"
  },
  "scalar_kind": null,
  "type_param_keys": [
    "Permissive.1f37a068c7c51aba23e9c41475c78eebc4e58471"
  ]
}'''

snapshots['test_multi_type_config_array_dict_fields[Selector] 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "List of Array.Selector.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "enum_values": null,
  "fields": null,
  "given_name": null,
  "key": "Array.Selector.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "kind": {
    "__enum__": "ConfigTypeKind.ARRAY"
  },
  "scalar_kind": null,
  "type_param_keys": [
    "Selector.1f37a068c7c51aba23e9c41475c78eebc4e58471"
  ]
}'''

snapshots['test_multi_type_config_array_dict_fields[Shape] 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "List of Array.Shape.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "enum_values": null,
  "fields": null,
  "given_name": null,
  "key": "Array.Shape.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "kind": {
    "__enum__": "ConfigTypeKind.ARRAY"
  },
  "scalar_kind": null,
  "type_param_keys": [
    "Shape.1f37a068c7c51aba23e9c41475c78eebc4e58471"
  ]
}'''

snapshots['test_multi_type_config_nested_dicts[nested_dict_types0] 1'] = '''{
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
      "name": "foo",
      "type_key": "Permissive.c1ae6abf6c3c9e951eeefe4fde820cafc053ee40"
    }
  ],
  "given_name": null,
  "key": "Selector.cb18f2a8fc9fa17668d8f4fd6b44c86c30c56774",
  "kind": {
    "__enum__": "ConfigTypeKind.SELECTOR"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_multi_type_config_nested_dicts[nested_dict_types1] 1'] = '''{
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
      "name": "foo",
      "type_key": "Shape.9bbda63934c371bf9be9a1cbb6fff9f5ee0be828"
    }
  ],
  "given_name": null,
  "key": "Selector.b188a7737a2fecf0fca8cf94d331be517176dddf",
  "kind": {
    "__enum__": "ConfigTypeKind.SELECTOR"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_multi_type_config_nested_dicts[nested_dict_types2] 1'] = '''{
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
      "name": "foo",
      "type_key": "Selector.c1ae6abf6c3c9e951eeefe4fde820cafc053ee40"
    }
  ],
  "given_name": null,
  "key": "Permissive.84180c8bd71a154af9d2965c8955925c228dc2bf",
  "kind": {
    "__enum__": "ConfigTypeKind.PERMISSIVE_SHAPE"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_multi_type_config_nested_dicts[nested_dict_types3] 1'] = '''{
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
      "name": "foo",
      "type_key": "Shape.3d03240a3cdb5557305a2118fb3a059896368dd1"
    }
  ],
  "given_name": null,
  "key": "Permissive.31f842392439e3c949b44f9e0e36bd1ed050a6b5",
  "kind": {
    "__enum__": "ConfigTypeKind.PERMISSIVE_SHAPE"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_multi_type_config_nested_dicts[nested_dict_types4] 1'] = '''{
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
      "name": "foo",
      "type_key": "Selector.9bbda63934c371bf9be9a1cbb6fff9f5ee0be828"
    }
  ],
  "given_name": null,
  "key": "Shape.88efc4d6ed14b1d35062d1e50a0227f606049e87",
  "kind": {
    "__enum__": "ConfigTypeKind.STRICT_SHAPE"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_multi_type_config_nested_dicts[nested_dict_types5] 1'] = '''{
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
      "name": "foo",
      "type_key": "Permissive.3d03240a3cdb5557305a2118fb3a059896368dd1"
    }
  ],
  "given_name": null,
  "key": "Shape.0117583609bbf6ddcd1b1c9586aca163c454ed9d",
  "kind": {
    "__enum__": "ConfigTypeKind.STRICT_SHAPE"
  },
  "scalar_kind": null,
  "type_param_keys": null
}'''

snapshots['test_pipeline_snap_all_props 1'] = '''{
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
      "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb": {
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
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb",
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
      "Shape.0bb49540f1708dcf5378009c9571eba999502e19": {
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
            "name": "io_manager",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
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
      "Shape.448bc7596c94071a7de00341f685ece16b2126cb": {
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
            "name": "noop_solid",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          }
        ],
        "given_name": null,
        "key": "Shape.448bc7596c94071a7de00341f685ece16b2126cb",
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
      "Shape.743e47901855cb245064dd633e217bfcb49a11a7": {
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
            "name": "config",
            "type_key": "Any"
          }
        ],
        "given_name": null,
        "key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7",
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
      "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727": {
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
            "name": "config",
            "type_key": "Any"
          },
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
        "key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727",
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
      "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"in_process\\": {}}",
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
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
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
            "default_value_as_json_str": "{\\"io_manager\\": {}}",
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"noop_solid\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.448bc7596c94071a7de00341f685ece16b2126cb"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
          }
        ],
        "given_name": null,
        "key": "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71",
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
        "is_dynamic_mapped": false,
        "solid_def_name": "noop_solid",
        "solid_name": "noop_solid",
        "tags": {}
      }
    ]
  },
  "description": "desc",
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
          "config_field_snap": {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "config",
            "type_key": "Any"
          },
          "description": null,
          "name": "io_manager"
        }
      ],
      "root_config_key": "Shape.f6ff50c7791bf4fa41de6c12d1b8d38c38ddcf71"
    }
  ],
  "name": "noop_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
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
  "tags": {
    "key": "value"
  }
}'''

snapshots['test_pipeline_snap_all_props 2'] = 'b1e5a50f73e7cbbdc0ec64fc42546f6ab64786a7'

snapshots['test_two_invocations_deps_snap 1'] = '''{
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
      "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb": {
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
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb",
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
      "Shape.05ee15830ea7c4d9f953920a207f3196207abc17": {
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
            "name": "one",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "two",
            "type_key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727"
          }
        ],
        "given_name": null,
        "key": "Shape.05ee15830ea7c4d9f953920a207f3196207abc17",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "scalar_kind": null,
        "type_param_keys": null
      },
      "Shape.0bb49540f1708dcf5378009c9571eba999502e19": {
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
            "name": "io_manager",
            "type_key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7"
          }
        ],
        "given_name": null,
        "key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "scalar_kind": null,
        "type_param_keys": null
      },
      "Shape.14cf82e55bf43102bea2cda8088841a632c6a14e": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"in_process\\": {}}",
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
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
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
            "default_value_as_json_str": "{\\"io_manager\\": {}}",
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.0bb49540f1708dcf5378009c9571eba999502e19"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{\\"one\\": {}, \\"two\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.05ee15830ea7c4d9f953920a207f3196207abc17"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.a2588a6acfaabe9de47899395c58b06786b9e2eb"
          }
        ],
        "given_name": null,
        "key": "Shape.14cf82e55bf43102bea2cda8088841a632c6a14e",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
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
      "Shape.743e47901855cb245064dd633e217bfcb49a11a7": {
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
            "name": "config",
            "type_key": "Any"
          }
        ],
        "given_name": null,
        "key": "Shape.743e47901855cb245064dd633e217bfcb49a11a7",
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
      "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727": {
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
            "name": "config",
            "type_key": "Any"
          },
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
        "key": "Shape.a7bc3a78db3c9e72a226493c8af08b4ac4dad727",
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
        "is_dynamic_mapped": false,
        "solid_def_name": "noop_solid",
        "solid_name": "one",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [],
        "is_dynamic_mapped": false,
        "solid_def_name": "noop_solid",
        "solid_name": "two",
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
          "config_field_snap": {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": false,
            "name": "config",
            "type_key": "Any"
          },
          "description": null,
          "name": "io_manager"
        }
      ],
      "root_config_key": "Shape.14cf82e55bf43102bea2cda8088841a632c6a14e"
    }
  ],
  "name": "two_solid_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": {
          "__class__": "ConfigFieldSnap",
          "default_provided": false,
          "default_value_as_json_str": null,
          "description": null,
          "is_required": false,
          "name": "config",
          "type_key": "Any"
        },
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
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
}'''

snapshots['test_two_invocations_deps_snap 2'] = '2ab347c3f075879e49bfc047b8f4c49f4e9f551d'

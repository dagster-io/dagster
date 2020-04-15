# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

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
        "type_param_keys": null
      },
      "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
        "__class__": "ConfigTypeSnap",
        "description": "List of [{ result?: { json: { path: Path } pickle: { path: Path } } }]",
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.ARRAY"
        },
        "type_param_keys": [
          "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
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
        "type_param_keys": null
      },
      "Path": {
        "__class__": "ConfigTypeSnap",
        "description": "",
        "enum_values": null,
        "fields": null,
        "given_name": "Path",
        "key": "Path",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR"
        },
        "type_param_keys": null
      },
      "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Bool",
          "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93"
        ]
      },
      "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Float",
          "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529"
        ]
      },
      "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Int",
          "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34"
        ]
      },
      "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "String",
          "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881"
        ]
      },
      "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
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
        "type_param_keys": null
      },
      "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          }
        ],
        "given_name": null,
        "key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Shape.11eb576307bebdc05b7f94a19ed6823cad2ba923": {
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
            "default_value_as_json_str": "{\\"noop_solid\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf"
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
        "key": "Shape.11eb576307bebdc05b7f94a19ed6823cad2ba923",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea": {
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
            "type_key": "Path"
          }
        ],
        "given_name": null,
        "key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
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
            "type_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6"
          }
        ],
        "given_name": null,
        "key": "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf": {
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
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          }
        ],
        "given_name": null,
        "key": "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05": {
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
            "type_key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
          }
        ],
        "given_name": null,
        "key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "input_hydration_schema_key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "is_builtin": true,
        "key": "Any",
        "kind": {
          "__enum__": "DagsterTypeKind.ANY"
        },
        "name": "Any",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Bool": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Bool",
        "input_hydration_schema_key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "is_builtin": true,
        "key": "Bool",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Bool",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Float": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Float",
        "input_hydration_schema_key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "is_builtin": true,
        "key": "Float",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Float",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Int": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Int",
        "input_hydration_schema_key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "is_builtin": true,
        "key": "Int",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Int",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Nothing": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Nothing",
        "input_hydration_schema_key": null,
        "is_builtin": true,
        "key": "Nothing",
        "kind": {
          "__enum__": "DagsterTypeKind.NOTHING"
        },
        "name": "Nothing",
        "output_materialization_schema_key": null,
        "type_param_keys": []
      },
      "Path": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Path",
        "input_hydration_schema_key": "Path",
        "is_builtin": true,
        "key": "Path",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Path",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "String": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "String",
        "input_hydration_schema_key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "is_builtin": true,
        "key": "String",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "String",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
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
        "solid_def_name": "noop_solid",
        "solid_name": "noop_solid",
        "tags": {}
      }
    ]
  },
  "description": "desc",
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
      "resource_def_snaps": []
    }
  ],
  "name": "noop_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Any",
            "description": null,
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
        "type_param_keys": null
      },
      "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
        "__class__": "ConfigTypeSnap",
        "description": "List of [{ result?: { json: { path: Path } pickle: { path: Path } } }]",
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.ARRAY"
        },
        "type_param_keys": [
          "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
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
        "type_param_keys": null
      },
      "Path": {
        "__class__": "ConfigTypeSnap",
        "description": "",
        "enum_values": null,
        "fields": null,
        "given_name": "Path",
        "key": "Path",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR"
        },
        "type_param_keys": null
      },
      "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Bool",
          "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93"
        ]
      },
      "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Float",
          "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529"
        ]
      },
      "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Int",
          "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34"
        ]
      },
      "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "String",
          "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881"
        ]
      },
      "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
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
        "type_param_keys": null
      },
      "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          }
        ],
        "given_name": null,
        "key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Shape.11eb576307bebdc05b7f94a19ed6823cad2ba923": {
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
            "default_value_as_json_str": "{\\"noop_solid\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf"
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
        "key": "Shape.11eb576307bebdc05b7f94a19ed6823cad2ba923",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea": {
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
            "type_key": "Path"
          }
        ],
        "given_name": null,
        "key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
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
            "type_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6"
          }
        ],
        "given_name": null,
        "key": "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf": {
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
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          }
        ],
        "given_name": null,
        "key": "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05": {
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
            "type_key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
          }
        ],
        "given_name": null,
        "key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "input_hydration_schema_key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "is_builtin": true,
        "key": "Any",
        "kind": {
          "__enum__": "DagsterTypeKind.ANY"
        },
        "name": "Any",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Bool": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Bool",
        "input_hydration_schema_key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "is_builtin": true,
        "key": "Bool",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Bool",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Float": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Float",
        "input_hydration_schema_key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "is_builtin": true,
        "key": "Float",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Float",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Int": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Int",
        "input_hydration_schema_key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "is_builtin": true,
        "key": "Int",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Int",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Nothing": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Nothing",
        "input_hydration_schema_key": null,
        "is_builtin": true,
        "key": "Nothing",
        "kind": {
          "__enum__": "DagsterTypeKind.NOTHING"
        },
        "name": "Nothing",
        "output_materialization_schema_key": null,
        "type_param_keys": []
      },
      "Path": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Path",
        "input_hydration_schema_key": "Path",
        "is_builtin": true,
        "key": "Path",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Path",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "String": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "String",
        "input_hydration_schema_key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "is_builtin": true,
        "key": "String",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "String",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
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
        "solid_def_name": "noop_solid",
        "solid_name": "noop_solid",
        "tags": {}
      }
    ]
  },
  "description": null,
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
      "resource_def_snaps": []
    }
  ],
  "name": "noop_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Any",
            "description": null,
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

snapshots['test_pipeline_snap_all_props 2'] = '634a36c067acaf9f10f37ac0ceb916d8c564160b'

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
        "type_param_keys": null
      },
      "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
        "__class__": "ConfigTypeSnap",
        "description": "List of [{ result?: { json: { path: Path } pickle: { path: Path } } }]",
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.ARRAY"
        },
        "type_param_keys": [
          "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
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
        "type_param_keys": null
      },
      "Path": {
        "__class__": "ConfigTypeSnap",
        "description": "",
        "enum_values": null,
        "fields": null,
        "given_name": "Path",
        "key": "Path",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR"
        },
        "type_param_keys": null
      },
      "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Bool",
          "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93"
        ]
      },
      "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Float",
          "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529"
        ]
      },
      "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Int",
          "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34"
        ]
      },
      "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "String",
          "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881"
        ]
      },
      "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
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
        "type_param_keys": null
      },
      "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          }
        ],
        "given_name": null,
        "key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Shape.0c3cca72f7600cd351847db4d50cfab8fa0fd170": {
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
            "default_value_as_json_str": "{\\"one\\": {}, \\"two\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.ff6673a2d8e7c67de99e344cd2ea2a603cb1fa5b"
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
        "key": "Shape.0c3cca72f7600cd351847db4d50cfab8fa0fd170",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea": {
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
            "type_key": "Path"
          }
        ],
        "given_name": null,
        "key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
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
            "type_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6"
          }
        ],
        "given_name": null,
        "key": "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05": {
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
            "type_key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
          }
        ],
        "given_name": null,
        "key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.ff6673a2d8e7c67de99e344cd2ea2a603cb1fa5b": {
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
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "two",
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          }
        ],
        "given_name": null,
        "key": "Shape.ff6673a2d8e7c67de99e344cd2ea2a603cb1fa5b",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "input_hydration_schema_key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "is_builtin": true,
        "key": "Any",
        "kind": {
          "__enum__": "DagsterTypeKind.ANY"
        },
        "name": "Any",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Bool": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Bool",
        "input_hydration_schema_key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "is_builtin": true,
        "key": "Bool",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Bool",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Float": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Float",
        "input_hydration_schema_key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "is_builtin": true,
        "key": "Float",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Float",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Int": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Int",
        "input_hydration_schema_key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "is_builtin": true,
        "key": "Int",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Int",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Nothing": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Nothing",
        "input_hydration_schema_key": null,
        "is_builtin": true,
        "key": "Nothing",
        "kind": {
          "__enum__": "DagsterTypeKind.NOTHING"
        },
        "name": "Nothing",
        "output_materialization_schema_key": null,
        "type_param_keys": []
      },
      "Path": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Path",
        "input_hydration_schema_key": "Path",
        "is_builtin": true,
        "key": "Path",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Path",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "String": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "String",
        "input_hydration_schema_key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "is_builtin": true,
        "key": "String",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "String",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
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
        "solid_def_name": "noop_solid",
        "solid_name": "one",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [],
        "solid_def_name": "noop_solid",
        "solid_name": "two",
        "tags": {}
      }
    ]
  },
  "description": null,
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
      "resource_def_snaps": []
    }
  ],
  "name": "two_solid_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Any",
            "description": null,
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

snapshots['test_two_invocations_deps_snap 2'] = 'd89efc442db557ae228f5e56016ff487ff1d43a6'

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
        "type_param_keys": null
      },
      "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
        "__class__": "ConfigTypeSnap",
        "description": "List of [{ result?: { json: { path: Path } pickle: { path: Path } } }]",
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.ARRAY"
        },
        "type_param_keys": [
          "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
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
        "type_param_keys": null
      },
      "Path": {
        "__class__": "ConfigTypeSnap",
        "description": "",
        "enum_values": null,
        "fields": null,
        "given_name": "Path",
        "key": "Path",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR"
        },
        "type_param_keys": null
      },
      "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Bool",
          "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93"
        ]
      },
      "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Float",
          "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529"
        ]
      },
      "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Int",
          "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34"
        ]
      },
      "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "String",
          "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881"
        ]
      },
      "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
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
        "type_param_keys": null
      },
      "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          }
        ],
        "given_name": null,
        "key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Shape.307d0350b12b8263b392969a8b6dfdbdf9e29e28": {
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
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "passtwo",
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "default_value_as_json_str": "{}",
            "description": null,
            "is_required": false,
            "name": "return_one",
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          }
        ],
        "given_name": null,
        "key": "Shape.307d0350b12b8263b392969a8b6dfdbdf9e29e28",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea": {
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
            "type_key": "Path"
          }
        ],
        "given_name": null,
        "key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
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
            "type_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6"
          }
        ],
        "given_name": null,
        "key": "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.bfdfd77baac9a6815ee5ed34e203f005aea52dd8": {
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
            "default_value_as_json_str": "{\\"passone\\": {}, \\"passtwo\\": {}, \\"return_one\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.307d0350b12b8263b392969a8b6dfdbdf9e29e28"
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
        "key": "Shape.bfdfd77baac9a6815ee5ed34e203f005aea52dd8",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05": {
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
            "type_key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
          }
        ],
        "given_name": null,
        "key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "input_hydration_schema_key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "is_builtin": true,
        "key": "Any",
        "kind": {
          "__enum__": "DagsterTypeKind.ANY"
        },
        "name": "Any",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Bool": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Bool",
        "input_hydration_schema_key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "is_builtin": true,
        "key": "Bool",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Bool",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Float": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Float",
        "input_hydration_schema_key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "is_builtin": true,
        "key": "Float",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Float",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Int": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Int",
        "input_hydration_schema_key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "is_builtin": true,
        "key": "Int",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Int",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Nothing": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Nothing",
        "input_hydration_schema_key": null,
        "is_builtin": true,
        "key": "Nothing",
        "kind": {
          "__enum__": "DagsterTypeKind.NOTHING"
        },
        "name": "Nothing",
        "output_materialization_schema_key": null,
        "type_param_keys": []
      },
      "Path": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Path",
        "input_hydration_schema_key": "Path",
        "is_builtin": true,
        "key": "Path",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Path",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "String": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "String",
        "input_hydration_schema_key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "is_builtin": true,
        "key": "String",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "String",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
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
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "result",
                "solid_name": "return_one"
              }
            ]
          }
        ],
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
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "result",
                "solid_name": "return_one"
              }
            ]
          }
        ],
        "solid_def_name": "passthrough",
        "solid_name": "passtwo",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [],
        "solid_def_name": "return_one",
        "solid_name": "return_one",
        "tags": {}
      }
    ]
  },
  "description": null,
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
      "resource_def_snaps": []
    }
  ],
  "name": "single_dep_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
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
            "is_required": true,
            "name": "result"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      },
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
        "description": null,
        "input_def_snaps": [],
        "name": "return_one",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Any",
            "description": null,
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

snapshots['test_basic_dep_fan_out 2'] = 'ab880e36b41951910b62fbf8608554c970bec0ba'

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
        "type_param_keys": null
      },
      "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
        "__class__": "ConfigTypeSnap",
        "description": "List of [{ result?: { json: { path: Path } pickle: { path: Path } } }]",
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.ARRAY"
        },
        "type_param_keys": [
          "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
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
        "type_param_keys": null
      },
      "Path": {
        "__class__": "ConfigTypeSnap",
        "description": "",
        "enum_values": null,
        "fields": null,
        "given_name": "Path",
        "key": "Path",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR"
        },
        "type_param_keys": null
      },
      "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Bool",
          "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93"
        ]
      },
      "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Float",
          "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529"
        ]
      },
      "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Int",
          "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34"
        ]
      },
      "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "String",
          "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881"
        ]
      },
      "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
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
        "type_param_keys": null
      },
      "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          }
        ],
        "given_name": null,
        "key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Shape.22ec23494d42efd1fc79b1c449e6ff51f1d1afbb": {
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
            "name": "take_nothings",
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          }
        ],
        "given_name": null,
        "key": "Shape.22ec23494d42efd1fc79b1c449e6ff51f1d1afbb",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea": {
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
            "type_key": "Path"
          }
        ],
        "given_name": null,
        "key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.4f02a5555bbcb7f76db149f86ba957c7da79ea80": {
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
            "default_value_as_json_str": "{\\"take_nothings\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.22ec23494d42efd1fc79b1c449e6ff51f1d1afbb"
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
        "key": "Shape.4f02a5555bbcb7f76db149f86ba957c7da79ea80",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
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
            "type_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6"
          }
        ],
        "given_name": null,
        "key": "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05": {
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
            "type_key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
          }
        ],
        "given_name": null,
        "key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "input_hydration_schema_key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "is_builtin": true,
        "key": "Any",
        "kind": {
          "__enum__": "DagsterTypeKind.ANY"
        },
        "name": "Any",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Bool": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Bool",
        "input_hydration_schema_key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "is_builtin": true,
        "key": "Bool",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Bool",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Float": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Float",
        "input_hydration_schema_key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "is_builtin": true,
        "key": "Float",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Float",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Int": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Int",
        "input_hydration_schema_key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "is_builtin": true,
        "key": "Int",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Int",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Nothing": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Nothing",
        "input_hydration_schema_key": null,
        "is_builtin": true,
        "key": "Nothing",
        "kind": {
          "__enum__": "DagsterTypeKind.NOTHING"
        },
        "name": "Nothing",
        "output_materialization_schema_key": null,
        "type_param_keys": []
      },
      "Path": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Path",
        "input_hydration_schema_key": "Path",
        "is_builtin": true,
        "key": "Path",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Path",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "String": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "String",
        "input_hydration_schema_key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "is_builtin": true,
        "key": "String",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "String",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
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
        "solid_def_name": "return_nothing",
        "solid_name": "nothing_one",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [],
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
        "solid_def_name": "take_nothings",
        "solid_name": "take_nothings",
        "tags": {}
      }
    ]
  },
  "description": null,
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
      "resource_def_snaps": []
    }
  ],
  "name": "fan_in_test",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
        "description": null,
        "input_def_snaps": [],
        "name": "return_nothing",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "result"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      },
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
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

snapshots['test_basic_fan_in 2'] = 'ad4ff4a4b528d6a1bfc6f296757f96bd5888e0d6'

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
        "type_param_keys": null
      },
      "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
        "__class__": "ConfigTypeSnap",
        "description": "List of [{ result?: { json: { path: Path } pickle: { path: Path } } }]",
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.ARRAY"
        },
        "type_param_keys": [
          "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
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
        "type_param_keys": null
      },
      "Path": {
        "__class__": "ConfigTypeSnap",
        "description": "",
        "enum_values": null,
        "fields": null,
        "given_name": "Path",
        "key": "Path",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR"
        },
        "type_param_keys": null
      },
      "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Bool",
          "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93"
        ]
      },
      "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Float",
          "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529"
        ]
      },
      "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "Int",
          "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34"
        ]
      },
      "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": null,
        "given_name": null,
        "key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SCALAR_UNION"
        },
        "type_param_keys": [
          "String",
          "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881"
        ]
      },
      "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
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
        "type_param_keys": null
      },
      "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
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
        "key": "Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
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
        "type_param_keys": null
      },
      "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6": {
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
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "default_value_as_json_str": null,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          }
        ],
        "given_name": null,
        "key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "kind": {
          "__enum__": "ConfigTypeKind.SELECTOR"
        },
        "type_param_keys": null
      },
      "Shape.11eb576307bebdc05b7f94a19ed6823cad2ba923": {
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
            "default_value_as_json_str": "{\\"noop_solid\\": {}}",
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf"
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
        "key": "Shape.11eb576307bebdc05b7f94a19ed6823cad2ba923",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea": {
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
            "type_key": "Path"
          }
        ],
        "given_name": null,
        "key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
        "type_param_keys": null
      },
      "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774": {
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
            "type_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6"
          }
        ],
        "given_name": null,
        "key": "Shape.67bfeb8716b5a1acfa25db8f46080919cb829774",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf": {
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
            "type_key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05"
          }
        ],
        "given_name": null,
        "key": "Shape.cfd4403245ea53e9035af8ce213022fec90f29bf",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "type_param_keys": null
      },
      "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05": {
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
            "type_key": "Array.Shape.67bfeb8716b5a1acfa25db8f46080919cb829774"
          }
        ],
        "given_name": null,
        "key": "Shape.e9ab42dd7e072d71d5b3be8febf5e4d8022dfc05",
        "kind": {
          "__enum__": "ConfigTypeKind.STRICT_SHAPE"
        },
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
        "input_hydration_schema_key": "Selector.ab6cd856d1a40704c2dc35f9933575746e9479e2",
        "is_builtin": true,
        "key": "Any",
        "kind": {
          "__enum__": "DagsterTypeKind.ANY"
        },
        "name": "Any",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Bool": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Bool",
        "input_hydration_schema_key": "ScalarUnion.Bool-Selector.931bb6ad8aa201c3e984966c80b27fb6679bef93",
        "is_builtin": true,
        "key": "Bool",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Bool",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Float": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Float",
        "input_hydration_schema_key": "ScalarUnion.Float-Selector.c4c3261d2cac02292e67855ef47c83ca58e42529",
        "is_builtin": true,
        "key": "Float",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Float",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Int": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Int",
        "input_hydration_schema_key": "ScalarUnion.Int-Selector.0154da9561ef717b75be37c4edd6ea9051b35a34",
        "is_builtin": true,
        "key": "Int",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Int",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "Nothing": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Nothing",
        "input_hydration_schema_key": null,
        "is_builtin": true,
        "key": "Nothing",
        "kind": {
          "__enum__": "DagsterTypeKind.NOTHING"
        },
        "name": "Nothing",
        "output_materialization_schema_key": null,
        "type_param_keys": []
      },
      "Path": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "Path",
        "input_hydration_schema_key": "Path",
        "is_builtin": true,
        "key": "Path",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "Path",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
        "type_param_keys": []
      },
      "String": {
        "__class__": "DagsterTypeSnap",
        "description": null,
        "display_name": "String",
        "input_hydration_schema_key": "ScalarUnion.String-Selector.e14649f87c389c8574a39812e1ff7dab2c8c5881",
        "is_builtin": true,
        "key": "String",
        "kind": {
          "__enum__": "DagsterTypeKind.SCALAR"
        },
        "name": "String",
        "output_materialization_schema_key": "Selector.fd35cd3159fffc7092f28f6efd65f706953c98f6",
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
        "solid_def_name": "noop_solid",
        "solid_name": "noop_solid",
        "tags": {}
      }
    ]
  },
  "description": null,
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
      "resource_def_snaps": []
    }
  ],
  "name": "noop_pipeline",
  "solid_definitions_snapshot": {
    "__class__": "SolidDefinitionsSnapshot",
    "composite_solid_def_snaps": [],
    "solid_def_snaps": [
      {
        "__class__": "SolidDefSnap",
        "config_field_snap": null,
        "description": null,
        "input_def_snaps": [],
        "name": "noop_solid",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Any",
            "description": null,
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

snapshots['test_empty_pipeline_snap_props 2'] = '88528edde2ed64da3c39cca0da8ba2f7586c1a5d'

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
      "type_key": "Selector.2d70a477fddef640dd26e7ded5d4317d66155b7f"
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
  "key": "Permissive.2922420c806e6864670c535462c974f498260ac4",
  "kind": {
    "__enum__": "ConfigTypeKind.PERMISSIVE_SHAPE"
  },
  "type_param_keys": null
}'''

snapshots['test_multi_type_config_array_dict_fields[Selector] 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "List of [{ bar: String foo: Int }]",
  "enum_values": null,
  "fields": null,
  "given_name": null,
  "key": "Array.Selector.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "kind": {
    "__enum__": "ConfigTypeKind.ARRAY"
  },
  "type_param_keys": [
    "Selector.1f37a068c7c51aba23e9c41475c78eebc4e58471"
  ]
}'''

snapshots['test_multi_type_config_array_dict_fields[Permissive] 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "List of [{ bar: String foo: Int }]",
  "enum_values": null,
  "fields": null,
  "given_name": null,
  "key": "Array.Permissive.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "kind": {
    "__enum__": "ConfigTypeKind.ARRAY"
  },
  "type_param_keys": [
    "Permissive.1f37a068c7c51aba23e9c41475c78eebc4e58471"
  ]
}'''

snapshots['test_multi_type_config_array_dict_fields[Shape] 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "List of [{ bar: String foo: Int }]",
  "enum_values": null,
  "fields": null,
  "given_name": null,
  "key": "Array.Shape.1f37a068c7c51aba23e9c41475c78eebc4e58471",
  "kind": {
    "__enum__": "ConfigTypeKind.ARRAY"
  },
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
  "type_param_keys": null
}'''

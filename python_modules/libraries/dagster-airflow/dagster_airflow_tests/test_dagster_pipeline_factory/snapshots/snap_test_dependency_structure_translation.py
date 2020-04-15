# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_one_task_dag 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator",
        "solid_name": "airflow_dummy_operator",
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
  "name": "airflow_one_task_dag",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

snapshots['test_two_task_dag_no_dep 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_1",
        "solid_name": "airflow_dummy_operator_1",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_2",
        "solid_name": "airflow_dummy_operator_2",
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
  "name": "airflow_two_task_dag_no_dep",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_1",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

snapshots['test_two_task_dag_with_dep 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_1",
        "solid_name": "airflow_dummy_operator_1",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_2",
        "solid_name": "airflow_dummy_operator_2",
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
  "name": "airflow_two_task_dag_with_dep",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_1",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

snapshots['test_diamond_task_dag 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_1",
        "solid_name": "airflow_dummy_operator_1",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_2",
        "solid_name": "airflow_dummy_operator_2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_3",
        "solid_name": "airflow_dummy_operator_3",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_2"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_3"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_4",
        "solid_name": "airflow_dummy_operator_4",
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
  "name": "airflow_diamond_task_dag",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_1",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_3",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_4",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

snapshots['test_multi_root_dag 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_1",
        "solid_name": "airflow_dummy_operator_1",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_2",
        "solid_name": "airflow_dummy_operator_2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_3",
        "solid_name": "airflow_dummy_operator_3",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_2"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_3"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_4",
        "solid_name": "airflow_dummy_operator_4",
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
  "name": "airflow_multi_root_dag",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_1",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_3",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_4",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

snapshots['test_multi_leaf_dag 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_dummy_operator_1",
        "solid_name": "airflow_dummy_operator_1",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_2",
        "solid_name": "airflow_dummy_operator_2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_3",
        "solid_name": "airflow_dummy_operator_3",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_dummy_operator_1"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_dummy_operator_4",
        "solid_name": "airflow_dummy_operator_4",
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
  "name": "airflow_multi_leaf_dag",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_1",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_3",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_dummy_operator_4",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

snapshots['test_complex_dag 1'] = '''{
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "disabled",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "in_process",
            "type_key": "Shape.ca5906d9a0377218b4ee7d940ad55957afa73d1b"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": true,
            "name": "pickle",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "filesystem",
            "type_key": "Shape.889b7348071b49700db678dab98bb0a15fd57ecd"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": true,
            "name": "json",
            "type_key": "Shape.4ce319f0b244b33c363530397798177d6b1ef2ea"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "description": null,
            "is_required": false,
            "name": "log_level",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.889b7348071b49700db678dab98bb0a15fd57ecd": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "marker_to_close",
            "type_key": "String"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
            "description": null,
            "is_required": false,
            "name": "max_concurrent",
            "type_key": "Int"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
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
      "Shape.d104239a91570c528e9ed6e83e99ad4268a10360": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "execution",
            "type_key": "Selector.4d63da53a40bb42f96aad27d25ec8a9656d40975"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "loggers",
            "type_key": "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "resources",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": true,
            "description": null,
            "is_required": false,
            "name": "solids",
            "type_key": "Shape.da39a3ee5e6b4b0d3255bfef95601890afd80709"
          },
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
            "description": null,
            "is_required": false,
            "name": "storage",
            "type_key": "Selector.efc7a1aa788fafe8121049790c968cbf2ebc247b"
          }
        ],
        "given_name": null,
        "key": "Shape.d104239a91570c528e9ed6e83e99ad4268a10360",
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
      "Shape.ebeaf4550c200fb540f2e1f3f2110debd8c4157c": {
        "__class__": "ConfigTypeSnap",
        "description": null,
        "enum_values": null,
        "fields": [
          {
            "__class__": "ConfigFieldSnap",
            "default_provided": false,
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
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_group"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_entry_gcs",
        "solid_name": "airflow_create_entry_gcs",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_entry_gcs_result",
        "solid_name": "airflow_create_entry_gcs_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_entry_gcs_result2",
        "solid_name": "airflow_create_entry_gcs_result2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": []
          }
        ],
        "solid_def_name": "airflow_create_entry_group",
        "solid_name": "airflow_create_entry_group",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_group"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_entry_group_result",
        "solid_name": "airflow_create_entry_group_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_group"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_entry_group_result2",
        "solid_name": "airflow_create_entry_group_result2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template_field"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag",
        "solid_name": "airflow_create_tag",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_result",
        "solid_name": "airflow_create_tag_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_result2",
        "solid_name": "airflow_create_tag_result2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_template",
        "solid_name": "airflow_create_tag_template",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_template_field",
        "solid_name": "airflow_create_tag_template_field",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template_field"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_template_field_result",
        "solid_name": "airflow_create_tag_template_field_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_template_result",
        "solid_name": "airflow_create_tag_template_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_create_tag_template_result2",
        "solid_name": "airflow_create_tag_template_result2",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_delete_entry_group"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_get_entry"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_lookup_entry"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_search_catalog"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_update_entry"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_delete_entry",
        "solid_name": "airflow_delete_entry",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_group"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_delete_tag_template"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_get_entry_group"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_search_catalog"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_delete_entry_group",
        "solid_name": "airflow_delete_entry_group",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_list_tags"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_search_catalog"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_update_tag"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_delete_tag",
        "solid_name": "airflow_delete_tag",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_delete_tag_template_field"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_get_tag_template"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_search_catalog"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_update_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_delete_tag_template",
        "solid_name": "airflow_delete_tag_template",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template_field"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_delete_tag"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_rename_tag_template_field"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_search_catalog"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_delete_tag_template_field",
        "solid_name": "airflow_delete_tag_template_field",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_get_entry",
        "solid_name": "airflow_get_entry",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_group"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_get_entry_group",
        "solid_name": "airflow_get_entry_group",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_get_entry_group"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_get_entry_group_result",
        "solid_name": "airflow_get_entry_group_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_get_entry"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_get_entry_result",
        "solid_name": "airflow_get_entry_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_get_tag_template",
        "solid_name": "airflow_get_tag_template",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_get_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_get_tag_template_result",
        "solid_name": "airflow_get_tag_template_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_list_tags",
        "solid_name": "airflow_list_tags",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_list_tags"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_list_tags_result",
        "solid_name": "airflow_list_tags_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_lookup_entry",
        "solid_name": "airflow_lookup_entry",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_lookup_entry"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_lookup_entry_result",
        "solid_name": "airflow_lookup_entry_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template_field"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_update_tag_template_field"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_rename_tag_template_field",
        "solid_name": "airflow_rename_tag_template_field",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_group"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              },
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template_field"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_search_catalog",
        "solid_name": "airflow_search_catalog",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_search_catalog"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_search_catalog_result",
        "solid_name": "airflow_search_catalog_result",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_entry_gcs"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_update_entry",
        "solid_name": "airflow_update_entry",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_update_tag",
        "solid_name": "airflow_update_tag",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_update_tag_template",
        "solid_name": "airflow_update_tag_template",
        "tags": {}
      },
      {
        "__class__": "SolidInvocationSnap",
        "input_dep_snaps": [
          {
            "__class__": "InputDependencySnap",
            "input_name": "airflow_task_ready",
            "upstream_output_snaps": [
              {
                "__class__": "OutputHandleSnap",
                "output_name": "airflow_task_complete",
                "solid_name": "airflow_create_tag_template_field"
              }
            ]
          }
        ],
        "solid_def_name": "airflow_update_tag_template_field",
        "solid_name": "airflow_update_tag_template_field",
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
  "name": "airflow_complex_dag",
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
            "dagster_type_key": "Nothing",
            "description": null,
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_entry_gcs",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_entry_gcs_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_entry_gcs_result2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_entry_group",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_entry_group_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_entry_group_result2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_result2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_template",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_template_field",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_template_field_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_template_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_create_tag_template_result2",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_delete_entry",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_delete_entry_group",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_delete_tag",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_delete_tag_template",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_delete_tag_template_field",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_get_entry",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_get_entry_group",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_get_entry_group_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_get_entry_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_get_tag_template",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_get_tag_template_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_list_tags",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_list_tags_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_lookup_entry",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_lookup_entry_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_rename_tag_template_field",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_search_catalog",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_search_catalog_result",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_update_entry",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_update_tag",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_update_tag_template",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
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
            "name": "airflow_task_ready"
          }
        ],
        "name": "airflow_update_tag_template_field",
        "output_def_snaps": [
          {
            "__class__": "OutputDefSnap",
            "dagster_type_key": "Nothing",
            "description": null,
            "is_required": true,
            "name": "airflow_task_complete"
          }
        ],
        "required_resource_keys": [],
        "tags": {}
      }
    ]
  },
  "tags": {}
}'''

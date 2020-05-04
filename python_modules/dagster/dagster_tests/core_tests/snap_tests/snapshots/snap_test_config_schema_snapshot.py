# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_historical_config_type_snap 1'] = '''{
  "__class__": "ConfigTypeSnap",
  "description": "",
  "enum_values": [],
  "fields": [],
  "given_name": "kjdkfjdkfjdkj",
  "key": "ksjdkfjdkfjd",
  "kind": {
    "__enum__": "ConfigTypeKind.STRICT_SHAPE"
  },
  "scalar_kind": null,
  "type_param_keys": []
}'''

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_mode_snap 1'] = '{"__class__": "ModeDefSnap", "description": "a_desc", "logger_def_snaps": [{"__class__": "LoggerDefSnap", "config_field_snap": null, "description": "logger_description", "name": "no_config_logger"}, {"__class__": "LoggerDefSnap", "config_field_snap": {"__class__": "ConfigFieldSnap", "default_provided": false, "default_value_as_json_str": null, "description": null, "is_required": true, "name": "config", "type_key": "Shape.6930c1ab2255db7c39e92b59c53bab16a55f80c1"}, "description": null, "name": "some_logger"}], "name": "a_mode", "resource_def_snaps": [{"__class__": "ResourceDefSnap", "config_field_snap": null, "description": null, "name": "io_manager"}, {"__class__": "ResourceDefSnap", "config_field_snap": null, "description": "resource_description", "name": "no_config_resource"}, {"__class__": "ResourceDefSnap", "config_field_snap": {"__class__": "ConfigFieldSnap", "default_provided": false, "default_value_as_json_str": null, "description": null, "is_required": true, "name": "config", "type_key": "Shape.4384fce472621a1d43c54ff7e52b02891791103f"}, "description": null, "name": "some_resource"}], "root_config_key": "Shape.b72d1e8186046ba83badce8fc22a3ad39a48f002"}'

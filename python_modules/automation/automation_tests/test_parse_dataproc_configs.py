import json
import os

from automation.parse_dataproc_configs import ConfigParser


def test_config_parser_job():
    curr_path = os.path.dirname(__file__)
    with open(os.path.join(curr_path, "__snapshots__", "schema.json"), "r", encoding="utf8") as f:
        json_schema = json.loads(f.read()).get("schemas")

    c = ConfigParser(json_schema)
    parsed = c.extract_schema_for_object("Job", "dataproc_job")
    assert parsed.configs.startswith(b"'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
    assert b"def define_dataproc_job_config():" in parsed.configs
    assert b"'sparkJob': Field(" in parsed.configs

    assert parsed.enums.startswith(b"'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
    assert b"State = Enum(" in parsed.enums
    assert b"Substate = Enum(" in parsed.enums

    c = ConfigParser(json_schema)
    parsed = c.extract_schema_for_object("ClusterConfig", "dataproc_cluster")
    assert parsed.configs.startswith(b"'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
    assert b"def define_dataproc_cluster_config():" in parsed.configs
    assert b"'masterConfig': Field(" in parsed.configs

    assert parsed.enums.startswith(b"'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
    assert b"Component = Enum(" in parsed.enums

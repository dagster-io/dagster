import os

from automation.parse_spark_configs import extract, serialize


def test_extract():
    curr_path = os.path.dirname(__file__)
    with open(os.path.join(curr_path, "__snapshots__", "spark_confs.md"), "r", encoding="utf8") as f:
        spark_conf_markdown = f.read()

    result = extract(spark_conf_markdown)
    assert not result.value
    assert list(result.children.keys()) == ["spark"]

    spark = result.children["spark"]
    assert sorted(list(spark.children.keys())) == [
        "app",
        "blacklist",
        "blockManager",
        "broadcast",
        "cleaner",
        "core",
        "cores",
        "default",
        "deploy",
        "driver",
        "dynamicAllocation",
        "eventLog",
        "executor",
        "extraListeners",
        "files",
        "graphx",
        "hadoop",
        "io",
        "jars",
        "kryo",
        "kryoserializer",
        "local",
        "locality",
        "log",
        "logConf",
        "master",
        "maxRemoteBlockSizeFetchToMem",
        "memory",
        "network",
        "port",
        "pyspark",
        "python",
        "r",
        "rdd",
        "redaction",
        "reducer",
        "rpc",
        "scheduler",
        "serializer",
        "shuffle",
        "speculation",
        "sql",
        "stage",
        "storage",
        "streaming",
        "submit",
        "task",
        "ui",
        "worker",
    ]


def test_serialize():
    curr_path = os.path.dirname(__file__)
    with open(os.path.join(curr_path, "__snapshots__", "spark_confs.md"), "r", encoding="utf8") as f:
        spark_conf_markdown = f.read()

    result = extract(spark_conf_markdown)

    serialized = serialize(result)
    assert b"def spark_config():" in serialized
    assert b"'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT\n\n" in serialized
    assert b"Application Properties: The name of your application." in serialized

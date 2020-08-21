from dagster_spark.utils import parse_spark_config


def test_parse_spark_config():
    test = {
        "spark": {
            "app": {"name": "foo"},
            "driver": {"blockManager": {}},
            "executor": {"pyspark": {}, "logs": {"rolling": {"time": {}}}},
            "local": {},
            "submit": {},
            "log": {},
            "executorEnv": {},
            "redaction": {},
            "python": {"profile": {}, "worker": {}},
            "files": {},
            "jars": {},
            "pyspark": {"driver": {}},
            "reducer": {},
            "shuffle": {
                "file": {},
                "io": {},
                "service": {"index": {"cache": {}}},
                "sort": {},
                "spill": {},
                "registration": {},
            },
            "eventLog": {"logBlockUpdates": {}, "longForm": {}, "buffer": {}},
            "ui": {"dagGraph": {}, "liveUpdate": {}},
            "worker": {"ui": {}},
            "sql": {"ui": {}},
            "streaming": {
                "ui": {},
                "backpressure": {},
                "receiver": {"writeAheadLog": {}},
                "kafka": {},
                "driver": {"writeAheadLog": {}},
            },
            "broadcast": {},
            "io": {"compression": {"lz4": {}, "snappy": {}, "zstd": {}}},
            "kryo": {},
            "kryoserializer": {"buffer": {}},
            "rdd": {},
            "serializer": {},
            "memory": {"offHeap": {}},
            "storage": {"replication": {}},
            "cleaner": {"periodicGC": {}, "referenceTracking": {"blocking": {}}},
            "default": {},
            "hadoop": {"mapreduce": {"fileoutputcommitter": {"algorithm": {}}}},
            "rpc": {"message": {}, "retry": {}},
            "blockManager": {},
            "network": {},
            "port": {},
            "core": {"connection": {"ack": {"wait": {}}}},
            "cores": {"max": "3"},
            "locality": {"wait": {}},
            "scheduler": {"revive": {}, "listenerbus": {"eventqueue": {}}},
            "blacklist": {"task": {}, "stage": {}, "application": {"fetchFailure": {}}},
            "speculation": {},
            "task": {"reaper": {}},
            "stage": {},
            "dynamicAllocation": {},
            "r": {"driver": {}, "shell": {}},
            "graphx": {"pregel": {}},
            "deploy": {"zookeeper": {}},
        }
    }
    parsed_config = parse_spark_config(test)

    # Iteration order isn't preserved across python versions
    assert set([("--conf", "spark.app.name=foo"), ("--conf", "spark.cores.max=3")]) == set(
        [(parsed_config[i], parsed_config[i + 1]) for i in range(0, len(parsed_config), 2)]
    )

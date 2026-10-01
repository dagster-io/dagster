import pytest
from dagster_spark.utils import construct_spark_shell_command, parse_spark_config

# Distinctive jar path used to locate the tail (application arguments) of the argv list.
JAR = "/path/to/app.jar"


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


def _application_arg_tokens(application_arguments):
    """Return the argv tokens that follow the jar, i.e. the application arguments."""
    cmd = construct_spark_shell_command(
        application_jar=JAR,
        main_class="com.example.Main",
        master_url="local[*]",
        spark_home="/opt/spark",
        application_arguments=application_arguments,
    )
    return cmd[cmd.index(JAR) + 1 :]


def test_construct_command_full_shape():
    """The full command is a flat argv list with each value as its own element."""
    cmd = construct_spark_shell_command(
        application_jar=JAR,
        main_class="com.example.Main",
        master_url="local[*]",
        deploy_mode="client",
        spark_conf={"spark": {"app": {"name": "my_app"}}},
        application_arguments="10 20",
        spark_home="/opt/spark",
    )
    assert cmd == [
        "/opt/spark/bin/spark-submit",
        "--class",
        "com.example.Main",
        "--master",
        "local[*]",
        "--deploy-mode",
        "client",
        "--conf",
        "spark.app.name=my_app",
        JAR,
        "10",
        "20",
    ]


@pytest.mark.parametrize(
    "application_arguments, expected_tokens",
    [
        # --- Legitimate usage that must keep working ---
        pytest.param("10", ["10"], id="single-arg"),
        pytest.param("10 20 30", ["10", "20", "30"], id="multiple-args"),
        pytest.param(
            "--local-path /tmp/dagster/events/data --date 2019-01-01",
            ["--local-path", "/tmp/dagster/events/data", "--date", "2019-01-01"],
            id="flags-and-values",
        ),
        pytest.param(
            '--query "SELECT * FROM t" --limit 10',
            ["--query", "SELECT * FROM t", "--limit", "10"],
            id="quoted-arg-with-spaces",
        ),
        # --- Shell features we intentionally NO LONGER interpret. Each of these
        # --- would previously have been acted on by /bin/sh; now they are passed
        # --- to spark-submit as literal, inert argv tokens.
        pytest.param("realarg ; id", ["realarg", ";", "id"], id="chain-semicolon"),
        pytest.param("a && b", ["a", "&&", "b"], id="chain-and"),
        pytest.param("a | b", ["a", "|", "b"], id="pipe"),
        pytest.param("out > /tmp/x", ["out", ">", "/tmp/x"], id="redirect"),
        pytest.param("$HOME", ["$HOME"], id="env-var-not-expanded"),
        pytest.param("~", ["~"], id="tilde-not-expanded"),
        pytest.param("*.jar", ["*.jar"], id="glob-not-expanded"),
        pytest.param("`whoami`", ["`whoami`"], id="backtick-substitution-not-run"),
        pytest.param("$(whoami)", ["$(whoami)"], id="dollar-paren-substitution-not-run"),
    ],
)
def test_application_arguments_are_tokenized_literally(application_arguments, expected_tokens):
    assert _application_arg_tokens(application_arguments) == expected_tokens


@pytest.mark.parametrize("application_arguments", [None, ""], ids=["none", "empty-string"])
def test_no_application_arguments_appends_nothing(application_arguments):
    assert _application_arg_tokens(application_arguments) == []

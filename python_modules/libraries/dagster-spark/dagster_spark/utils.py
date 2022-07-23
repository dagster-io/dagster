import itertools
import os

import dagster._check as check

from .types import SparkOpError


def flatten_dict(d):
    def _flatten_dict(d, result, key_path=None):
        """Iterates an arbitrarily nested dictionary and yield dot-notation key:value tuples.

        {'foo': {'bar': 3, 'baz': 1}, {'other': {'key': 1}} =>
            [('foo.bar', 3), ('foo.baz', 1), ('other.key', 1)]

        """
        for k, v in d.items():
            new_key_path = (key_path or []) + [k]
            if isinstance(v, dict):
                _flatten_dict(v, result, new_key_path)
            else:
                result.append((".".join(new_key_path), v))

    result = []
    if d is not None:
        _flatten_dict(d, result)
    return result


def parse_spark_config(spark_conf):
    """For each key-value pair in spark conf, we need to pass to CLI in format:

    --conf "key=value"
    """

    spark_conf_list = flatten_dict(spark_conf)
    return format_for_cli(spark_conf_list)


def format_for_cli(spark_conf_list):
    return list(
        itertools.chain.from_iterable([("--conf", "{}={}".format(*c)) for c in spark_conf_list])
    )


def construct_spark_shell_command(
    application_jar,
    main_class,
    master_url=None,
    spark_conf=None,
    deploy_mode=None,
    application_arguments=None,
    spark_home=None,
):
    """Constructs the spark-submit command for a Spark job."""
    check.opt_str_param(master_url, "master_url")
    check.str_param(application_jar, "application_jar")
    spark_conf = check.opt_dict_param(spark_conf, "spark_conf")
    check.opt_str_param(deploy_mode, "deploy_mode")
    check.opt_str_param(application_arguments, "application_arguments")
    check.opt_str_param(spark_home, "spark_home")

    spark_home = spark_home if spark_home else os.environ.get("SPARK_HOME")
    if spark_home is None:
        raise SparkOpError(
            (
                "No spark home set. You must either pass spark_home in config or "
                "set $SPARK_HOME in your environment (got None)."
            )
        )

    master_url = ["--master", master_url] if master_url else []
    deploy_mode = ["--deploy-mode", deploy_mode] if deploy_mode else []

    spark_shell_cmd = (
        ["{}/bin/spark-submit".format(spark_home), "--class", main_class]
        + master_url
        + deploy_mode
        + parse_spark_config(spark_conf)
        + [application_jar]
        + [application_arguments]
    )
    return spark_shell_cmd

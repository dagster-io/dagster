import itertools


def flatten_dict(d):
    def _flatten_dict(d, result, key_path=None):
        '''Iterates an arbitrarily nested dictionary and yield dot-notation key:value tuples.

        {'foo': {'bar': 3, 'baz': 1}, {'other': {'key': 1}} =>
            [('foo.bar', 3), ('foo.baz', 1), ('other.key', 1)]

        '''
        for k, v in d.items():
            new_key_path = (key_path or []) + [k]
            if isinstance(v, dict):
                _flatten_dict(v, result, new_key_path)
            else:
                result.append(('.'.join(new_key_path), v))

    result = []
    if d is not None:
        _flatten_dict(d, result)
    return result


def parse_spark_config(spark_conf):
    '''For each key-value pair in spark conf, we need to pass to CLI in format:

        --conf "key=value"
    '''

    spark_conf_list = flatten_dict(spark_conf)
    return format_for_cli(spark_conf_list)


def format_for_cli(spark_conf_list):
    return list(
        itertools.chain.from_iterable([('--conf', '{}={}'.format(*c)) for c in spark_conf_list])
    )

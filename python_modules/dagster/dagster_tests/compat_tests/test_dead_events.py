from os import path

from dagster.core.serdes import deserialize_json_to_dagster_namedtuple


def test_dead_events():
    snapshot = path.join(path.dirname(path.realpath(__file__)), 'dead_events.txt')
    with open(snapshot, 'r') as fd:
        objs = []
        for line in fd.readlines():
            obj = deserialize_json_to_dagster_namedtuple(line)
            assert obj is not None
            objs.append(obj)

    assert len(objs) == 6

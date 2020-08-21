from os import path

from dagster.serdes import deserialize_value


def test_dead_events():
    snapshot = path.join(path.dirname(path.realpath(__file__)), "dead_events.txt")
    with open(snapshot, "r") as fd:
        objs = []
        for line in fd.readlines():
            obj = deserialize_value(line)
            assert obj is not None
            objs.append(obj)

    assert len(objs) == 6

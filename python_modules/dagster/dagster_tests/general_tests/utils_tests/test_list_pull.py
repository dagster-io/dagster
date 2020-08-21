from collections import namedtuple

from dagster.utils import list_pull


def test_list_pull():
    assert list_pull([], "foo") == []


def test_list_pull_dicts():
    test_data = [{"foo": "bar1"}, {"foo": "bar2"}]

    assert list_pull(test_data, "foo") == ["bar1", "bar2"]


def test_pull_objects():
    TestObject = namedtuple("TestObject", "bar")
    test_objs = [TestObject(bar=2), TestObject(bar=3)]
    assert list_pull(test_objs, "bar") == [2, 3]

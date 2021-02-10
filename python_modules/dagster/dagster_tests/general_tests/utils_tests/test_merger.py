from dagster.utils.merger import deep_merge_dicts, merge_dicts


def test_simple_merge():
    assert deep_merge_dicts({}, {}) == {}
    assert deep_merge_dicts({1: 2}, {}) == {1: 2}
    assert deep_merge_dicts({}, {1: 2}) == {1: 2}


def test_nested_merge():
    from_dict = {"key": {"nested_one": 1}}

    onto_dict = {"key": {"nested_two": 2}}

    assert deep_merge_dicts(onto_dict, from_dict) == {"key": {"nested_one": 1, "nested_two": 2}}


def test_nested_override_merge():
    from_dict = {"key": {"nested_one": 1}}

    onto_dict = {"key": {"nested_one": 2}}

    assert deep_merge_dicts(onto_dict, from_dict) == {"key": {"nested_one": 1}}


def test_smash():
    from_dict = {"value": "smasher"}
    onto_dict = {"value": "got_smashed"}

    assert deep_merge_dicts(onto_dict, from_dict)["value"] == "smasher"


def test_realistic():
    from_dict = {
        "context": {
            "unittest": {
                "resources": {
                    "db_resource": {"config": {"user": "some_user", "password": "some_password"}}
                }
            }
        }
    }

    onto_dict = {"context": {"unittest": {"resources": {"another": {"config": "not_sensitive"}}}}}

    result_dict = {
        "context": {
            "unittest": {
                "resources": {
                    "db_resource": {"config": {"user": "some_user", "password": "some_password"}},
                    "another": {"config": "not_sensitive"},
                }
            }
        }
    }

    assert deep_merge_dicts(onto_dict, from_dict) == result_dict


def test_merge():
    # two element merge
    assert merge_dicts({}, {}) == {}
    assert merge_dicts({1: 2}, {}) == {1: 2}
    assert merge_dicts({}, {1: 2}) == {1: 2}
    assert merge_dicts({1: 1}, {1: 2}) == {1: 2}

    # three element merge
    assert merge_dicts({}, {}, {}) == {}
    assert merge_dicts({1: 2}, {2: 3}, {3: 4}) == {1: 2, 2: 3, 3: 4}
    assert merge_dicts({1: 2}, {1: 3}, {1: 4}) == {1: 4}

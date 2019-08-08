from dagster import check


def checks_for_helper_functions(computeContribs, parseNeighbors):
    check.callable_param(computeContribs, 'computeContribs')
    check.callable_param(parseNeighbors, 'parseNeighbors')

    assert parseNeighbors('foo bar') == ('foo', 'bar')
    assert list(computeContribs(['a', 'b', 'c', 'd'], 1.0)) == [
        ('a', 0.25),
        ('b', 0.25),
        ('c', 0.25),
        ('d', 0.25),
    ]

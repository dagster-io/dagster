# Vendored from https://gitlab.com/ericvsmith/toposort/-/blob/master/src/toposort.py?ref_type=heads
#######################################################################
# Implements a topological sort algorithm.
#
# Copyright 2014-2021 True Blade Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Notes:
#  Based on http://code.activestate.com/recipes/578272-topological-sort
#   with these major changes:
#    Added unittests.
#    Deleted doctests (maybe not the best idea in the world, but it cleans
#     up the docstring).
#    Moved functools import to the top of the file.
#    Changed assert to a ValueError.
#    Changed iter[items|keys] to [items|keys], for python 3
#     compatibility. I don't think it matters for python 2 these are
#     now lists instead of iterables.
#    Copy the input so as to leave it unmodified.
#    Renamed function from toposort2 to toposort.
#    Handle empty input.
#    Switch tests to use set literals.
#
########################################################################

__all__ = ["toposort", "toposort_flatten", "CircularDependencyError"]
__version__ = "1.10"


class CircularDependencyError(ValueError):
    def __init__(self, data):
        s = f"Circular dependencies exist among these items: {{{', '.join(f'{key}:{value}' for key, value in data.items())}}}"
        super(CircularDependencyError, self).__init__(s)
        self.data = data


def toposort(data):
    """\
Dependencies are expressed as a dictionary whose keys are items
    and whose values are a set of dependent items. Output is a list of
    sets in topological order. The first set consists of items with no
    dependences, each subsequent set consists of items that depend upon
    items in the preceeding sets.
    """
    # Special case empty input.
    if len(data) == 0:
        return

    # Copy the input so as to leave it unmodified.
    # Discard self-dependencies and copy two levels deep.
    data = {item: set(e for e in dep if e != item) for item, dep in data.items()}

    # Find all items that don't depend on anything.
    extra_items_in_deps = {value for values in data.values() for value in values} - set(data.keys())
    # The line below does N unions of value sets, which is much slower than the
    # set comprehension above which does 1 union of N value sets. The speedup
    # gain is around 200x on a graph with 190k nodes.
    # extra_items_in_deps = _reduce(set.union, data.values()) - set(data.keys())

    # Add empty dependences where needed.
    data.update({item: set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item, dep in data.items() if len(dep) == 0)
        if not ordered:
            break
        yield ordered
        data = {item: (dep - ordered) for item, dep in data.items() if item not in ordered}
    if len(data) != 0:
        raise CircularDependencyError(data)


def toposort_flatten(data, sort=True):
    """\
Returns a single list of dependencies. For any set returned by
    toposort(), those items are sorted and appended to the result (just to
    make the results deterministic).
    """
    result = []
    for d in toposort(data):
        result.extend((sorted if sort else list)(d))
    return result

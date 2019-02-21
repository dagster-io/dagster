'''Always-sorted wrappers around toposort.'''
import toposort as toposort_


def toposort(data):
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data):
    return [item for level in toposort(data) for item in level]

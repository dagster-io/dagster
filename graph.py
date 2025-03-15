from collections.abc import Sequence
from typing import Any, Optional


class Graph:
    ...
    # @classmethod
    # def step(cls, name: str, deps: Optional[Sequence[Any]] = None):
    #     def _inner(fn):
    #         setattr(fn, "__step_name__", "name")
    #         return fn

    #     if deps:
    #         import code

    #         code.interact(local=locals())

    #     return _inner


def graph_step(name: str, deps: Optional[Sequence[Any]] = None):
    def _inner(fn):
        setattr(fn, "__step_name__", "name")
        return fn

    if deps:
        import code

        code.interact(local=locals())

    return _inner


class SpecificGraph(Graph):
    @graph_step(name="step_one")
    def step_one(self): ...

    @graph_step(name="step_two", deps=[step_one])
    def step_two(self): ...

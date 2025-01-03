from typing import (
    Annotated,
    Any,
    ForwardRef,
    List,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import dagster._check as check


def is_type(obj: Any) -> bool:
    return (
        # Normie types
        isinstance(obj, type)
        or
        # Covers Union, Optional, and Literal
        get_origin(obj) is not None
        or
        # Covers ForwardRef
        isinstance(obj, ForwardRef)
        or
        # Covers TypeVar
        isinstance(obj, TypeVar)
    )


def assert_is_type(obj: Any) -> Type[Any]:
    if not is_type(obj):
        check.failed(f"Expected type got {obj} which is {type(obj)}")
    return obj


def unwrap_type(type_: Type[Any]) -> Type[Any]:
    # Resolve TypeVars
    if isinstance(type_, TypeVar):
        bounds = type_.__constraints__
        if not bounds:
            # REVIEW: this is probably too ambiguous and worth raising
            return type(Any)
        return unwrap_type(bounds[0])

    # Filter out NoneTypes because all fields are optional in capnproto
    if get_origin(type_) is Union and type(None) in get_args(type_):
        non_none_types = {t for t in get_args(type_) if t is not type(None)}
        if len(non_none_types) == 1:
            return unwrap_type(next(iter(non_none_types)))
        else:
            return unwrap_type(Union[tuple(non_none_types)])  # type: ignore no idea what it's talking about

    # Remove metadata from Annotated types
    if get_origin(type_) is Annotated:
        return unwrap_type(get_args(type_)[0])

    return type_


def simple_type(type_: type) -> type:
    origin = get_origin(type_)
    if origin is None:
        return type_
    return origin


def find_repeated_subtree(
    type_: type, pruned_root: type, subtree_grafts: List[Tuple[type, int]]
) -> Tuple[Union[type, ForwardRef], Set[int]]:
    if isinstance(type_, ForwardRef):
        # assume any forward refs are recursive, this is should be true if you're
        # using get_type_hints to get the root type
        passed = {
            level - 1
            for level, subtree_graft in subtree_grafts
            if simple_type(pruned_root) == simple_type(subtree_graft)
        }
        return (ForwardRef("self"), {level for level in passed if level >= 0})

    origin = get_origin(type_)
    args = get_args(type_)
    if origin is None or args is None:
        passed = {
            level - 1
            for subtree_graft, level in subtree_grafts
            if simple_type(type_) == simple_type(subtree_graft)
        }
        return (type_, {level for level in passed if level >= 0})

    # pair the args with the grafts, a graft is a subtree (type) that could be a match
    next_grafts = [[] for _ in args]
    for subtree_graft, level in (*subtree_grafts, (pruned_root, 0)):
        graft_origin = simple_type(subtree_graft)
        graft_args = get_args(subtree_graft)

        if origin == graft_origin and not graft_args:
            # short circuit the search
            return (type_, set([level - 1]))
        elif origin == graft_origin and len(args) == len(graft_args):
            # continue the search
            for next_graft, graft in zip(next_grafts, graft_args):
                next_graft.append((graft, level + 1))
        else:
            # no match
            continue

    new_args = []
    raw_results = []
    intersecting_matches = None
    for arg, next_graft in zip(args, next_grafts):
        new_arg, matches = find_repeated_subtree(arg, pruned_root, next_graft)
        raw_results.append((new_arg, matches))
        intersecting_matches = (
            matches if intersecting_matches is None else (intersecting_matches & matches)
        )
        new_args.append(new_arg)

    should_return_ref = (intersecting_matches is not None) and (0 in intersecting_matches)
    intersecting_matches = (
        {level - 1 for level in intersecting_matches if level > 0}
        if intersecting_matches is not None
        else set()
    )
    if should_return_ref:
        return (ForwardRef("self"), intersecting_matches)
    return (origin[tuple(new_args)], intersecting_matches)


def normalize_type(type_: type) -> type:
    origin = get_origin(type_)
    if origin is None:
        return type_

    args = get_args(type_)
    if args is None:
        return type_

    new_args = []
    for arg in args:
        new_arg, _ = find_repeated_subtree(arg, type_, [])
        new_args.append(new_arg)
    return origin[tuple(new_args)]

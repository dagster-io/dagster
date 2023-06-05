import random

from dagster import AutoMaterializePolicy, asset, repository, SkipReason


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_upstream():
    return 3


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_1(eager_upstream):
    return eager_upstream + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
def lazy_upstream():
    return 1


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
def lazy_downstream_1(lazy_upstream):
    return lazy_upstream + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
def lazy_downstream_2(lazy_upstream):
    return lazy_upstream + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_2_skipper(eager_downstream_1):
    random.seed(5438790)
    if random.randint(0, 10) < 8:
        return SkipReason("Testing")
    return eager_downstream_1 + 1


@repository
def auto_materialize_repo_1():
    return [
        eager_upstream,
        eager_downstream_1,
        lazy_upstream,
        lazy_downstream_1,
        lazy_downstream_2,
        eager_downstream_2_skipper,
    ]

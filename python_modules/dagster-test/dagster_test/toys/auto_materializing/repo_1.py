from dagster import AutoMaterializePolicy, asset, repository


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_upstream():
    return 1


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_1(eager_upstream):
    return eager_upstream + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
def lazy_upstream():
    return 1


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
def lazy_downstream_1(lazy_upstream):
    return lazy_upstream + 1


@repository
def auto_materialize_repo_1():
    return [eager_upstream, eager_downstream_1, lazy_upstream, lazy_downstream_1]

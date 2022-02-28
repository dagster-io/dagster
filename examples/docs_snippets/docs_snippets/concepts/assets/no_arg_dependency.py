import pickle

from dagster import asset


@asset
def upstream_asset():
    with open("upstream_asset.pkl", "wb", encoding="utf8") as f:
        pickle.dump([1, 2, 3], f)


@asset(non_argument_deps={"upstream_asset"})
def downstream_asset():
    with open("upstream_asset.pkl", "wb", encoding="utf8") as f:
        data = pickle.load(f)

    with open("downstream_asset.pkl", "wb", encoding="utf8") as f:
        pickle.dump(f, data + [4])

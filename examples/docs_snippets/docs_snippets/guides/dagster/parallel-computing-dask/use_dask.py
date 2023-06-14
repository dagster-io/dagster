# isort: skip_file
from dask.distributed import Client
from dagster import ConfigurableResource


class DaskResource(ConfigurableResource):
    def make_dask_cluster(self) -> Client:
        client = Client()
        return client


## first_ex_start
from dagster import asset, MetadataValue, Definitions


@asset
def simple_dask_asset(context, MyDaskResource: DaskResource):
    client = MyDaskResource.make_dask_cluster()

    def square(x):
        return x**2

    def neg(x):
        return -x

    A = client.map(square, range(10000))
    B = client.map(neg, A)
    total = client.submit(sum, B)
    return total.result()


defs = Definitions(
    assets=[simple_dask_asset], resources={"MyDaskResource": DaskResource()}
)
## first_ex_end

## hackernew_ex_start

from dagster import asset, MetadataValue
import requests
import dask
import pandas as pd


@asset
def hackernews_stories_dask(context, MyDaskResource: DaskResource):
    client = MyDaskResource.make_dask_cluster()
    latest_item = requests.get(
        "https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()
    results = []
    scope = range(latest_item - 1000, latest_item)

    @dask.delayed
    def get_single_line(item_id):
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        return item

    for item_id in scope:
        y = dask.delayed(get_single_line)(item_id)
        results.append(y)

    results = dask.compute(*results)
    df = pd.DataFrame(results)
    context.add_output_metadata({"volume": len(df)})
    client.close()
    return df


## hackernew_ex_end

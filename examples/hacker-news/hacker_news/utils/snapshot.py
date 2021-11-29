import gzip
import json
from concurrent.futures import ThreadPoolExecutor

from dagster.utils import file_relative_path
from hacker_news.resources.hn_resource import HNAPIClient
from tqdm import tqdm

# Slice that surrounds 12/30/2020
SNAPSHOT_START_ID = 25576000
SNAPSHOT_END_ID = 25582000


if __name__ == "__main__":

    client = HNAPIClient()
    ids = range(SNAPSHOT_START_ID, SNAPSHOT_END_ID)
    with ThreadPoolExecutor() as executor:
        results = list(tqdm(executor.map(client.fetch_item_by_id, ids), total=len(ids)))

    items = {}
    for x in results:
        items[int(x["id"])] = x

    with gzip.open(file_relative_path(__file__, "../snapshot.gzip"), "w") as f:
        f.write(json.dumps(items).encode())

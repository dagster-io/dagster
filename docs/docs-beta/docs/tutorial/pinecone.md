---
title: Pinecone
description: Use Dagster to upload data into Pinecone
last_update:
  date: 2024-12-30
  author: Dennis Hume
---

## Overview
Many AI applications are data applications. Organizations want to leverage existing LLMs rather than build their own. But in order to take advantage of all the models that exist, you need to supplement them with your own data to produce more accurate and contextually aware results. We will demonstrate how to use Dagster to extract data, generate embeddings, and store the results within a vector database ([Pinecone](https://www.pinecone.io/)) which we can then use to power AI models to craft far more detailed answers.

### Dagster Concepts

- [resources](/todo)
- [run configurations](/todo)

### Services

- [DuckDB](/todo)
- [Pinecone](/todo)

## Code

![Pinecone asset graph](/images/tutorials/pinecone/pinecone_dag.png)

### Setup

All the code for this tutorial can be found at [project_dagster_pinecone](/todo).

Install the project dependencies:
```
pip install -e ".[dev]"
```

Run Dagster:
```
dagster dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Loading Data
We will be working with review data from Goodreads. These reviews exist as a collection of JSON files categorized by different genres. We will focus on just the files for graphic novels to limit the size of the files we will process. Within this domain, the files we will be working with are `goodreads_books_comics_graphic.json.gz` and `goodreads_reviews_comics_graphic.json.gz`. Since the data is normalized across these two files, we will want to combine information before feeding it into our vector database.

One way to handle preprocessing of the data is with [DuckDB](https://duckdb.org/). DuckDB is an in-process database, similar to SQLite, optimized for analytical workloads. We will start by creating two Dagster assets to load in the data. Each will load one of the files and create a DuckDB table (`graphic_novels` and `reviews`):

<CodeExample
  pathPrefix="tutorial_pinecone/tutorial_pinecone"
  filePath="assets.py" 
  lineStart="22"
  lineEnd ="60"
  />

With our DuckDB tables created, we can now query them like any other SQL table. Our third asset will join and filter the data and then return a DataFrame (we will also `LIMIT` the results to 500):
```python
# asssets.py
@dg.asset(
    kinds={"duckdb"},
    group_name="ingestion",
)
def enriched_reviews(
    duckdb_resource: dg_duckdb.DuckDBResource,
    graphic_novels,
    reviews,
) -> pd.DataFrame:
    query = f"""
        select
          reviews.review_id as review_id,
          graphic_novels.title as title,
          reviews.rating as rating,
          reviews.review_text as text
        from graphic_novels
        left join reviews
          on graphic_novels.book_id = reviews.book_id
        where graphic_novels.language_code = 'eng'
        limit 500
    """
    with duckdb_resource.get_connection() as conn:
        return conn.execute(query).fetch_df()
```

Now that the data has been prepared, we are ready to work with our vector database.

### Vector Database
We can begin by creating the index within our vector database. A vector database is a specialized database designed to store, manage, and retrieve high-dimensional vector embeddings, enabling efficient similarity search and machine learning tasks. There are many different vector databases available. For this demo we will use Pinecone which is a cloud based vector database that offers a [free tier](https://app.pinecone.io/) that can help us get started.

:::note
After you have your API key from Pinecone. You will want to set it to the environment variable `PINECONE_API_KEY`:
```
export PINECONE_API_KEY={YOUR PINECONE API KEY}
```
:::

Now that we have a Pinecone account we can incorporate Pinecone into our code. To help make everything consistent, we will create a Pinecone resource similar to the Dagster maintained DuckDB resource we used to ingest the Goodreads data. Creating a custom resource is fairly simple, the only information we need to authenticate with the Pinecone client is their API key: 
```python
#resources.py
class PineconeResource(ConfigurableResource):
    api_key: str = Field(
        description=(
            "Pinecone API key. See https://docs.pinecone.io/reference/api/introduction"
        )
    )

    _client: Pinecone = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = Pinecone(
            api_key=self.api_key,
        )
    ...
```

For our methods we will want the ability to create an index, retrieve a index so we can upsert records, and the ability to embed inputs. You can see all the details in the repo but this is what the `create_index` method looks like:
```python
#resources.py
    def create_index(
        self,
        index_name: str,
        dimension: int,
        metric: str,
        serverless_spec: ServerlessSpec,
    ):
        existing_indexes = [
            index_info["name"] for index_info in self._client.list_indexes()
        ]

        if index_name not in existing_indexes:
            self._client.create_index(
                index_name,
                dimension=dimension,
                metric=metric,
                spec=serverless_spec,
            )
            while not self._client.describe_index(index_name).status["ready"]:
                time.sleep(1)
```

With our Pinecone resource complete, we can initialize it using the API key that we set the environment variable for:
```python
# resources.py
pinecone_resource = PineconeResource(api_key=dg.EnvVar("PINECONE_API_KEY"))
```

Using our Pinecone resource it is easy enough to create an asset to manage the index where we will upload our embeddings:
```python
# assets.py
@dg.asset(
    kinds={"Pinecone"},
    group_name="processing",
)
def pinecone_index(
    pinecone_resource: PineconeResource,
):
    spec = ServerlessSpec(cloud="aws", region="us-east-1")
    pinecone_resource.create_index(
        INDEX_NAME,
        dimension=1024,
        metric="cosine",
        serverless_spec=spec,
    )
```

### Generate Embeddings
Between our data and the index, we are ready to create and upload our embeddings. One final asset will bring this all together. We will iterate through DataFrame from `enriched_reviews` and generate embeddings for each review. Then we can include additional metadata that will be the final vectors we upload to Pinecone using our Pinecone resource.

```python
# assets.py
@dg.asset(
    kinds={"Pinecone"},
    group_name="processing",
)
def pinecone_embeddings(
    pinecone_resource: PineconeResource,
    enriched_reviews: pd.DataFrame,
    pinecone_index,
):
    data = enriched_reviews.to_dict("records")

    vectors = []
    for chunk in _chunks(data, 50):

        embeddings = pinecone_resource.embed(
            inputs=[r["text"] for r in chunk],
            input_type="passage",
        )

        for d, e in zip(chunk, embeddings):
            vectors.append(
                {
                    "id": str(d["review_id"]),
                    "values": e["values"],
                    "metadata": {
                        "source": "goodreads",
                        "rating": d["rating"],
                        "title": d["title"],
                        "text": d["text"],
                    },
                }
            )

    pinecone_resource.index(INDEX_NAME).upsert(
        vectors=vectors,
        namespace=NAMESPACE,
    )
```

Those 5 assets are all we need to create and populate our index within Pinecone. We can combine these assets together into a job and execute them all together:
```python
# jobs.py
goodreads_pinecone = dg.define_asset_job(
    name="goodreads_pinecone",
    selection=[
        assets.graphic_novels,
        assets.reviews,
        assets.enriched_reviews,
        assets.pinecone_index,
        assets.pinecone_embeddings,
    ],
)
```

![Pinecone job](/images/tutorials/pinecone/pinecone_job.png)

In the Dagster UI go to **Job** and select **goodreads_pinecone** and click the **Materialize all** button. If this is the first time running the job, it may take a minute or so to process the data.

### Building AI Assets
Populating our vector database is only one part of our workflow. We can also build assets that query that index. We will look at one final asset that is separate from the `goodreads_pinecone` job. This asset is called `graphic_novel_search` which allows us to run queries and get the most similar results based on the reviews. We might want to ask many different questions using this asset so we will include a run configuration so we can execute many different questions:
```python
#assets.py
class GoodreadsQuestion(dg.Config):
    question: str
    top_k: int

@dg.asset(
    kinds={"Pinecone"},
    group_name="retrieval",
)
def graphic_novel_search(
    context: dg.AssetExecutionContext,
    config: GoodreadsQuestion,
    pinecone_resource: PineconeResource,
    pinecone_embeddings,
):
    query_embedding = pinecone_resource.embed(
        inputs=[config.question],
        input_type="query",
    )
    index = pinecone_resource.index(INDEX_NAME)
    results = index.query(
        namespace=NAMESPACE,
        vector=query_embedding[0].values,
        top_k=config.top_k,
        include_values=False,
        include_metadata=True,
    )
    for result in results["matches"]:
        context.log.info(result)
```

Again we are using the Pinecone resource, though this time we are querying rather than uploading results. Within the Dagster UI we can execute this asset by itself. Since this asset has a run configuration, we will have to set that before we can materialize a run. Feel free to experiment but we will ask it to find a scary graphic novel:
```
ops:
  graphic_novel_search:
    config:
      question: A scary graphic novel
      top_k: 1
```

After materializing the asset you can view the logs to see the output of what was the best match:
```
{'id': '37b6d106-2223-f7b9-c9b7-c4bfc4867dc1',
 'metadata': {'rating': 4.0,
              'source': 'goodreads',
              'text': 'Dark and disturbing, yet many of the panels are '
                      'gorgeously illustrated. A promising start!',
              'title': 'Wytches, Volume 1'},
 'score': 0.852409363,
 'values': []}
```

# Going Forward
This was a relatively simple example but you see the amount of coordination that is needed to power realworld AI applications. As you add more and more sources of unstructured data that updates on different cadences and powers multiple downstream tasks you will want to think of operational details for building around AI.

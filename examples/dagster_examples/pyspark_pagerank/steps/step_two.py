import re
from operator import add

from pyspark.sql import SparkSession

from dagster import InputDefinition, pipeline, solid


def computeContribs(urls, rank):
    """Calculates URL contributions to the rank of other URLs."""
    num_urls = len(urls)
    for url in urls:
        yield (url, rank / num_urls)


def parseNeighbors(urls):
    """Parses a urls pair string into urls pair."""
    parts = re.split(r'\s+', urls)
    return parts[0], parts[1]


@solid(input_defs=[InputDefinition('pagerank_data', str)])
def whole_pipeline_solid(context, pagerank_data):
    # Initialize the spark context.
    spark = SparkSession.builder.appName("PythonPageRank").getOrCreate()

    context.log.info('Page rank data path {}'.format(pagerank_data))

    # two urls per line with space in between)
    lines = spark.read.text(pagerank_data).rdd.map(lambda r: r[0])

    context.log.info('Page rank data {}'.format(lines))

    # Loads all URLs from input file and initialize their neighbors.
    links = lines.map(parseNeighbors).distinct().groupByKey().cache()

    # Loads all URLs with other URL(s) link to from input file and initialize ranks of them to one.
    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 1.0))

    iterations = 2

    # Calculates and updates URL ranks continuously using PageRank algorithm.
    for _iteration in range(iterations):
        # Calculates URL contributions to the rank of other URLs.
        contribs = links.join(ranks).flatMap(
            lambda url_urls_rank: computeContribs(url_urls_rank[1][0], url_urls_rank[1][1])
        )

        # Re-calculates URL ranks based on neighbor contributions.
        ranks = contribs.reduceByKey(add).mapValues(lambda rank: rank * 0.85 + 0.15)

    # Collects all URL ranks and dump them to console.
    for (link, rank) in ranks.collect():
        context.log.info("%s has rank: %s." % (link, rank))

    collected_ranks = ranks.collect()

    spark.stop()

    return collected_ranks


@pipeline
def pyspark_pagerank_step_two():
    whole_pipeline_solid()

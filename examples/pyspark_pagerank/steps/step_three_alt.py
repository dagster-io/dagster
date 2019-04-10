import re
from operator import add

from pyspark.sql import SparkSession

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    Path,
    PipelineDefinition,
    solid,
)

from dagster_pyspark import SparkRDD

'''
Steps:

0) Imports
1) Extract out load_pagerank_data_step_three_alt. End with lines.map(parseNeighbors)
2) Change signature to:
@solid(inputs=[InputDefinition('path', Path)], outputs=[OutputDefinition(SparkRDD)])
def load_pagerank_data_step_three_alt(_context, path):
3) Add solids and dep graph to pipeline def
'''


def computeContribs(urls, rank):
    """Calculates URL contributions to the rank of other URLs."""
    num_urls = len(urls)
    for url in urls:
        yield (url, rank / num_urls)


def parseNeighbors(urls):
    """Parses a urls pair string into urls pair."""
    parts = re.split(r'\s+', urls)
    return parts[0], parts[1]


@solid(inputs=[InputDefinition('path', Path)], outputs=[OutputDefinition(SparkRDD)])
def load_pagerank_data_step_three_alt(_context, path):
    spark = SparkSession.builder.appName("PythonPageRank").getOrCreate()

    # two urls per line with space in between)
    lines = spark.read.text(path).rdd.map(lambda r: r[0])

    # Loads all URLs from input file and initialize their neighbors.
    return lines.map(parseNeighbors)


@solid(inputs=[InputDefinition('urls', SparkRDD)])
def execute_page_rank_step_three_alt(context, urls):
    # Initialize the spark context.
    spark = SparkSession.builder.appName("PythonPageRank").getOrCreate()

    # Loads all URLs from input file and initialize their neighbors.
    links = urls.distinct().groupByKey().cache()

    # Loads all URLs with other URL(s) link to from input file and initialize ranks of them to one.
    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 1.0))

    iterations = 2

    # Calculates and updates URL ranks continuously using PageRank algorithm.
    for _ in range(iterations):
        # Calculates URL contributions to the rank of other URLs.
        contribs = links.join(ranks).flatMap(
            lambda url_urls_rank: computeContribs(url_urls_rank[1][0], url_urls_rank[1][1])
        )

        # Re-calculates URL ranks based on neighbor contributions.
        ranks = contribs.reduceByKey(add).mapValues(lambda rank: rank * 0.85 + 0.15)

    # Collects all URL ranks and dump them to console.
    for (link, rank) in ranks.collect():
        context.log.info("%s has rank: %s." % (link, rank))

    spark.stop()


def define_pyspark_pagerank_step_three():
    return PipelineDefinition(
        name='pyspark_pagerank_step_three',
        solids=[load_pagerank_data_step_three_alt, execute_page_rank_step_three_alt],
        dependencies={
            'execute_page_rank_step_three_alt': {
                'urls': DependencyDefinition('load_pagerank_data_step_three_alt')
            }
        },
    )


if __name__ == '__main__':
    from dagster import execute_pipeline
    from dagster.utils import script_relative_path

    execute_pipeline(
        define_pyspark_pagerank_step_three(),
        environment_dict={
            'solids': {
                'whole_pipeline_solid': {
                    'inputs': {'path': script_relative_path('../pagerank_data.txt')}
                }
            }
        },
    )

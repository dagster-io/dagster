import re
from operator import add

from dagster import (
    Dict,
    DependencyDefinition,
    Field,
    Int,
    InputDefinition,
    OutputDefinition,
    Path,
    PipelineContextDefinition,
    PipelineDefinition,
    solid,
)

from dagster_framework.pyspark import spark_session_resource, SparkRDD


def parseNeighbors(urls):
    """Parses a urls pair string into urls pair."""
    parts = re.split(r'\s+', urls)
    return parts[0], parts[1]


@solid(inputs=[InputDefinition('pagerank_data', Path)], outputs=[OutputDefinition(SparkRDD)])
def parse_pagerank_data(context, pagerank_data):
    lines = context.resources.spark.read.text(pagerank_data).rdd.map(lambda r: r[0])
    return lines.map(parseNeighbors)


@solid(inputs=[InputDefinition('urls', SparkRDD)], outputs=[OutputDefinition(SparkRDD)])
def compute_links(_context, urls):
    # lines = context.resources.spark.read.text(pagerank_data).rdd.map(lambda r: r[0])
    # links = lines.map(parseNeighbors).distinct().groupByKey().cache()
    # return links

    return urls.distinct().groupByKey().cache()


def computeContribs(urls, rank):
    """Calculates URL contributions to the rank of other URLs."""
    num_urls = len(urls)
    for url in urls:
        yield (url, rank / num_urls)


@solid(
    inputs=[InputDefinition(name='links', dagster_type=SparkRDD)],
    outputs=[OutputDefinition(name='ranks', dagster_type=SparkRDD)],
    config_field=Field(Dict({'iterations': Field(Int, is_optional=True, default_value=1)})),
)
def calculate_ranks(context, links):
    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 1.0))

    iterations = context.solid_config['iterations']
    for iteration in range(iterations):
        # Calculates URL contributions to the rank of other URLs.
        contribs = links.join(ranks).flatMap(
            lambda url_urls_rank: computeContribs(url_urls_rank[1][0], url_urls_rank[1][1])
        )

        # Re-calculates URL ranks based on neighbor contributions.
        ranks = contribs.reduceByKey(add).mapValues(lambda rank: rank * 0.85 + 0.15)
        context.log.info('Completed iteration {}'.format(iteration))

    return ranks


@solid(inputs=[InputDefinition(name='ranks', dagster_type=SparkRDD)], outputs=[])
def log_ranks(context, ranks):
    for (link, rank) in ranks.collect():
        context.log.info("%s has rank: %s." % (link, rank))


def define_pipeline():
    return PipelineDefinition(
        name='pyspark_pagerank',
        context_definitions={
            'local': PipelineContextDefinition(resources={'spark': spark_session_resource})
        },
        solids=[parse_pagerank_data, compute_links, calculate_ranks, log_ranks],
        dependencies={
            'compute_links': {'urls': DependencyDefinition('parse_pagerank_data')},
            'calculate_ranks': {'links': DependencyDefinition('compute_links')},
            'log_ranks': {'ranks': DependencyDefinition('calculate_ranks', 'ranks')},
        },
    )

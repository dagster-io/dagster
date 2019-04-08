import re
from operator import add

from pyspark.sql import SparkSession

from dagster import (
    Dict,
    DependencyDefinition,
    Field,
    Int,
    InputDefinition,
    OutputDefinition,
    Result,
    Path,
    PipelineContextDefinition,
    PipelineDefinition,
    resource,
    solid,
)
from dagster.core.types.runtime import define_any_type

from dagster_framework.spark.configs_spark import spark_config

from dagster_framework.spark.utils import flatten_dict


@resource(config_field=Field(Dict({'spark_conf': spark_config()})))
def spark_session_resource(init_context):
    builder = SparkSession.builder
    flat = flatten_dict(init_context.resource_config['spark_conf'])
    for key, value in flat:
        builder = builder.config(key, value)

    spark = builder.getOrCreate()
    try:
        yield spark
    finally:
        spark.stop()


SparkRDD = define_any_type('SparkRDD')


def parseNeighbors(urls):
    """Parses a urls pair string into urls pair."""
    parts = re.split(r'\s+', urls)
    return parts[0], parts[1]


@solid(inputs=[InputDefinition('pagerank_data', Path)], outputs=[OutputDefinition(SparkRDD)])
def compute_links(context, pagerank_data):
    lines = context.resources.spark.read.text(pagerank_data).rdd.map(lambda r: r[0])
    links = lines.map(parseNeighbors).distinct().groupByKey().cache()
    return links


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
        solids=[compute_links, calculate_ranks, log_ranks],
        dependencies={
            'calculate_ranks': {'links': DependencyDefinition('compute_links')},
            'log_ranks': {'ranks': DependencyDefinition('calculate_ranks', 'ranks')},
        },
    )

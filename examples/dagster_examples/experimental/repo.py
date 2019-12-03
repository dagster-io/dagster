from dagster_gcp import bigquery_resource
from dagster_pandas import DataFrame
from dagster_slack import slack_resource

from dagster import (
    EventMetadataEntry,
    ExpectationResult,
    Field,
    List,
    Materialization,
    ModeDefinition,
    Output,
    OutputDefinition,
    RepositoryDefinition,
    pipeline,
    solid,
)

sql_queries = [
    '''
    SELECT
        DATE(block_timestamp) AS transaction_date,
        SUM(output_value)/100000000 AS DASH_transferred
    FROM
        `bigquery-public-data.crypto_dash.transactions`
    WHERE
        DATE(block_timestamp) = '{date}'
    GROUP BY
        transaction_date
    ''',
    '''
    SELECT
        DATE(timestamp) as block_date,
        COUNT(*) as DASH_blocks
    FROM
        `bigquery-public-data.crypto_dash.blocks`
    WHERE
        DATE(timestamp) = '{date}'
    GROUP BY
        block_date
    ''',
]


@solid(
    output_defs=[OutputDefinition(List[DataFrame])],
    config={'date': Field(str)},
    required_resource_keys={'bigquery'},
    metadata={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
)
def bq_solid(context):  # pylint: disable=unused-argument
    date = context.solid_config.get('date')

    # Retrieve results as pandas DataFrames
    results = []
    for sql_query in sql_queries:
        sql_query = sql_query.format(date=date)
        context.log.info('executing query %s' % (sql_query))
        results.append(context.resources.bigquery.query(sql_query).to_dataframe())

    return results


@solid(required_resource_keys={'slack'})
def send_to_slack(context, download_data):

    transaction_data = download_data[0]
    block_data = download_data[1]

    transaction_date = transaction_data['transaction_date'][0]
    block_date = block_data['block_date'][0]

    yield ExpectationResult(
        label='dates_match',
        success=transaction_date == block_date,
        metadata_entries=[
            EventMetadataEntry.text(str(transaction_date), 'transaction_date'),
            EventMetadataEntry.text(str(block_date), 'block_date'),
        ],
    )

    date = transaction_date
    dash_transferred = transaction_data['DASH_transferred'][0]
    dash_blocks = block_data['DASH_blocks'][0]
    average_dash_transferred_per_block = float(dash_transferred) / dash_blocks

    yield Materialization(
        label='data',
        metadata_entries=[
            EventMetadataEntry.text(
                '{dash_transferred} dash tranferred'.format(dash_transferred=dash_transferred),
                'dash_transferred',
            ),
            EventMetadataEntry.text(
                '{dash_blocks} dash blocks'.format(dash_blocks=dash_blocks), 'dash_blocks'
            ),
        ],
    )

    context.resources.slack.chat.post_message(
        channel='#metrics-testing',
        text='{date}\nDash Transferred: {dash_transferred}\nDash blocks: {dash_blocks}\n'
        'Average dash transferred/block: {average_dash_transferred_per_block}'.format(
            date=date,
            dash_transferred=dash_transferred,
            dash_blocks=dash_blocks,
            average_dash_transferred_per_block=average_dash_transferred_per_block,
        ),
    )

    yield Output(1)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='default', resource_defs={'bigquery': bigquery_resource, 'slack': slack_resource}
        )
    ]
)
def dash_stats():
    send_to_slack(bq_solid())


@solid(config={'partition': Field(str)})
def announce_partition(context):
    context.log.info(str(context.pipeline_run.tags.get('dagster/partition')))
    context.log.info(context.solid_config.get('partition'))


@pipeline
def log_partitions():
    announce_partition()


def define_repo():
    return RepositoryDefinition(
        name='experimental_repository', pipeline_defs=[dash_stats, log_partitions]
    )

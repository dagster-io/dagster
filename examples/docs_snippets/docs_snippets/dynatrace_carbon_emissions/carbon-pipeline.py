from dagster import pipeline, solid, execute_pipeline, ModeDefinition
from dagster_dynatrace.resources import dynatrace_resource
from itertools import groupby
import json
import datetime
import time

TECH_MAPPING = {
    'Cl_Cas': 'Cassandra',
    'Cl_ES': 'ElasticSearch',
    'Cl_Ser': 'Dynatrace-Node',
    'Cl_PSG': 'ActiveGate-Node',
    'SYN': 'Synthetic',
}

# ref: https://www.goclimate.com/blog/the-carbon-footprint-of-servers/
# Cloud server using 100% green electricity: 160 kg CO2e / year and server
# Cloud server using non-green electricity: 381 kg CO2e / year and server
# On premise or data center-server using 100% green electricity: 320 kg CO2e / year and server
# On premise or data center-server using non-green electricity: 761 kg CO2e / year and server
CLOUD_TYPE_COST = {
    'EC2': 381,
    'AZURE': 170,
    'GOOGLE_CLOUD_PLATFORM': 160,
}

class DTEntity:
    def __init__(self, data):
        self._data = data

    @property
    def tags(self):
        return self._data.get('tags', [])

    def has_tag(self, tag):
        return len(list(filter(lambda t: t.get('key') == tag, self.tags))) > 0

    @property
    def technology(self):
        for tag, tech in TECH_MAPPING.items():
            if self.has_tag(tag):
                return tech
        return ''

    @property
    def cloudType(self):
        return self._data.get('properties', {}).get('cloudType', '')

    @property
    def id(self):
        return self._data['entityId']

    @property
    def clusterName(self):
        cluster_tag_key = 'Cluster.Name'

        if self.has_tag(cluster_tag_key):
            cluster_tags = list(filter(lambda t: t['key'] == cluster_tag_key, self.tags))

            return cluster_tags[0].get('value', '')

        return ''

    def estimate(self):
        # do something better here
        try:
            return CLOUD_TYPE_COST[self.cloudType]
        except KeyError:
            import random

            return 761 * random.random()

    def __str__(self):
        return self._data['displayName']


def _estimate(cloud_type):
    return CLOUD_TYPE_COST.get(cloud_type, CLOUD_TYPE_COST.get(None))


@solid
def estimate_infrastructure(context, entities: list) -> list:
    emissions_per_entity = []

    for entity in entities:
        emissions_per_entity.append(DTEntity(entity))

    context.log.info(f'Found {len(entities)} entities')

    return emissions_per_entity


@solid(required_resource_keys={'dynatrace'})
def fetch_entities_from_dynatrace(context):
    dt_data = context.resources.dynatrace.client.entities(data={
        "entitySelector": 'type(HOST)',
        "pageSize": 4000,
        "fields": "properties,tags,managementZones"
    })

    entities = dt_data.get('entities', [])

    return entities


@solid(required_resource_keys={'dynatrace'})
def push_metrics_to_dynatrace(context, emissions):
    def group_key(e):
        return e.cloudType, e.clusterName, e.technology

    emissions.sort(key=group_key)

    data = []

    for attributes, entities in groupby(emissions, group_key):
        dimensions = {
            'cloudtype': attributes[0],
            'clustername': attributes[1],
            'technology': attributes[2]
        }

        dt = datetime.datetime.now()
        unix_millis = time.mktime(dt.timetuple()) * 1000

        for e in entities:
            data.append({
                'metric_key': 'infra.tests',
                'value': e.estimate(),
                'dimensions': dimensions,
                'timestamp': unix_millis,
            })

    resp = context.resources.dynatrace.set_multiple_metrics(data)

    context.log.info(json.dumps(resp))


@solid(required_resource_keys={'dynatrace'})
def push_metrics_to_dt_v1(context, entities):
    timeseries = []
    dimension_keys = ['cloudtype', 'clustername', 'technology']

    for e in entities:
        attrs = (e.cloudType, e.clusterName, e.technology)

        dimensions = {
            'cloudtype': attrs[0],
            'clustername': attrs[1],
            'technology': attrs[2]
        }

        for k in dimensions.keys():
            if not dimensions[k]:
                dimensions[k] = 'unknown'

        dt = datetime.datetime.now()
        unix_millis = time.mktime(dt.timetuple()) * 1000

        timeseries.append({
            "timeseriesId": 'custom:infra.emission',
            "dimensions": dimensions,
            "dataPoints": [
                [unix_millis, e.estimate()]
            ]
        })

    resp = context.resources.dynatrace.set_metrics_v1('custom:infra.emission', timeseries, dimension_keys)


@pipeline(mode_defs=[ModeDefinition(resource_defs={'dynatrace': dynatrace_resource})])
def co2_aggregate_pipeline():
    entities = fetch_entities_from_dynatrace()
    emissions = estimate_infrastructure(entities)
    push_metrics_to_dynatrace(emissions)
    push_metrics_to_dt_v1(emissions)


if __name__ == '__main__':
    result = execute_pipeline(
        co2_aggregate_pipeline
    )

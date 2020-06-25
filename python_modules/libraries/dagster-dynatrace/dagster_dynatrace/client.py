from urllib.parse import urljoin
import requests
import datetime, time

class DTClient:
    def __init__(self, token, host):
        self.token = token
        self.host = host

    def build_url_v1(self, endpoint):
        return urljoin(self.host, f'api/v1/{endpoint}')


    def build_url(self, endpoint):
        return urljoin(self.host, f'api/v2/{endpoint}')


    def build_headers(self):
        return {
            'Authorization': f'Api-Token {self.token}',
            'Content-Type': 'text/plain; charset=utf-8'
        }

    def create_metric_v1(self, metric_key, display_name, dimensions, types=["Dagster"]):
        headers = self.build_headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        data = {
            'displayName': f'{display_name}',
            'unit': 'Count',
            'dimensions': dimensions,
            'types': types
        }
        resp = requests.put(self.build_url_v1('timeseries/' + metric_key), json=data, headers=headers)

        resp.raise_for_status()

        return resp.json()


    def push_metric_v1(self, metric_key, dimensions, values, type="Dagster"):
        self.create_metric_v1(metric_key, metric_key, dimensions)

        headers = self.build_headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        data = {
            'displayName': f'dagster_{metric_key}',
            'group': type,
            'type': type,
            'series': values
        }

        resp = requests.post(self.build_url_v1('entity/infrastructure/custom/dagster_' + metric_key), json=data, headers=headers)

        resp.raise_for_status()

        return resp.json()


    def push(self, data, endpoint):
        resp = requests.post(self.build_url(endpoint), data=data, headers=self.build_headers())

        resp.raise_for_status()

        return resp.json()


    def pull(self, entities, endpoint):
        metricSelector = entities

        if type(entities) is list:
            metricSelector = ','.join(entities)

        headers = self.build_headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        params = {
            'metricSelector': metricSelector,
        }

        resp = requests.get(f'{self.build_url(endpoint)}', params=params, headers=headers)

        resp.raise_for_status()

        return resp.json()


    def entities(self, data):
        endpoint = 'entities'
        headers = self.build_headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'

        resp = requests.get(f'{self.build_url(endpoint)}', params=data, headers=headers)

        resp.raise_for_status()

        return resp.json()

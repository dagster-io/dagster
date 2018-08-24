import os
from graphql.execution.executors.asyncio import AsyncioExecutor
from flask import Flask, send_file, send_from_directory
from flask_graphql import GraphQLView
from flask_cors import CORS

from dagster import check
from dagster.cli.repository_config import (
    RepositoryInfo,
    reload_repository_info,
)

from .schema import create_schema


class RepositoryContainer:
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repository_info):
        self.repository_info = check.inst_param(repository_info, 'repository_info', RepositoryInfo)

    def reload(self):
        self.repository_info = reload_repository_info(self.repository_info)

    @property
    def repository(self):
        return self.repository_info.repository


class DagsterGraphQLView(GraphQLView):
    def __init__(self, repository_container, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.repository_container = check.inst_param(
            repository_container,
            'repository_container',
            RepositoryContainer,
        )

    def get_context(self):
        return {'repository_container': self.repository_container}


def static_view(path, file):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), './webapp/build/static/', path), file
    )


def index_view(_path):
    return send_file(os.path.join(os.path.dirname(__file__), './webapp/build/index.html'))


def create_app(repository_container):
    app = Flask('dagster-ui')

    schema = create_schema()
    app.add_url_rule(
        '/graphql', 'graphql',
        DagsterGraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True,
            executor=AsyncioExecutor(),
            repository_container=repository_container,
        )
    )
    app.add_url_rule('/static/<path:path>/<string:file>', 'static_view', static_view)
    app.add_url_rule('/<path:_path>', 'index_catchall', index_view)
    app.add_url_rule(
        '/',
        'index',
        index_view,
        defaults={'_path': ''},
    )

    CORS(app)

    return app

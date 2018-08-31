import os
from graphql.execution.executors.asyncio import AsyncioExecutor
from flask import Flask, send_file, send_from_directory
from flask_graphql import GraphQLView
from flask_cors import CORS

from dagster import (
    check,
    RepositoryDefinition,
)

from dagster.cli.context import RepositoryInfo

from .schema import create_schema


class DagsterGraphQLView(GraphQLView):
    def __init__(self, repository_container, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.repository_container = repository_container
        # self.repository = check.inst_param(repository, 'repository', RepositoryDefinition)

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

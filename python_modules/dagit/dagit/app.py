import os
from graphql.execution.executors.asyncio import AsyncioExecutor
from flask import Flask, send_file, send_from_directory
from flask_graphql import GraphQLView
from flask_cors import CORS

from .schema import create_schema


class DagsterGraphQLView(GraphQLView):
    def __init__(self, pipeline_config=None, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.pipeline_config = pipeline_config

    def get_context(self):
        return {'pipeline_config': self.pipeline_config}


def static_view(path, file):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), './webapp/build/static/', path), file
    )


def index_view(_path):
    return send_file(os.path.join(os.path.dirname(__file__), './webapp/build/index.html'))


def create_app(pipeline_config):
    app = Flask('dagster-ui')

    schema = create_schema()
    app.add_url_rule(
        '/graphql', 'graphql',
        DagsterGraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True,
            executor=AsyncioExecutor(),
            pipeline_config=pipeline_config,
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

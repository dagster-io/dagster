from graphql.execution.executors.asyncio import AsyncioExecutor
from flask import Flask
from flask_graphql import GraphQLView
from flask_cors import CORS

from .schema import create_schema


class DagsterGraphQLView(GraphQLView):
    def __init__(self, pipeline_config=None, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.pipeline_config = pipeline_config

    def get_context(self):
        return {'pipeline_config': self.pipeline_config}


def create_app(pipeline_config):
    app = Flask('dagster-ui')

    schema = create_schema()
    app.add_url_rule(
        '/graphql',
        view_func=DagsterGraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True,
            executor=AsyncioExecutor(),
            pipeline_config=pipeline_config,
        )
    )

    CORS(app)

    return app

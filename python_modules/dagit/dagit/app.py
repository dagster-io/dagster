import os
try:
    from graphql.execution.executors.asyncio import AsyncioExecutor as Executor
except ImportError:
    from graphql.execution.executors.thread import ThreadExecutor as Executor
from flask import Flask, send_file, send_from_directory
from flask_graphql import GraphQLView
from flask_cors import CORS

from dagster import check

from dagster.cli.dynamic_loader import (
    DynamicObject,
    reload_pipeline_or_repo,
)

from .schema import create_schema


class RepositoryContainer(object):
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repo_dynamic_obj):
        self.repo_dynamic_obj = check.inst_param(
            repo_dynamic_obj,
            'repo_dynamic_obj',
            DynamicObject,
        )

    def reload(self):
        self.repo_dynamic_obj = reload_pipeline_or_repo(self.repo_dynamic_obj)

    @property
    def repository(self):
        return self.repo_dynamic_obj.object


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
    try:
        return send_file(os.path.join(os.path.dirname(__file__), './webapp/build/index.html'))
    except FileNotFoundError:
        text = """<p>Can't find webapp files. Probably webapp isn't built. If you are using dagit, then probably it's a corrupted installation or a bug. However, if you are developing dagit locally, you problem can be fixed as follows:</p>

<pre>cd ./python_modules/dagit/dagit/webapp
yarn
yarn build</pre>"""
        return text, 500


def create_app(repository_container):
    app = Flask('dagster-ui')

    schema = create_schema()
    app.add_url_rule(
        '/graphql', 'graphql',
        DagsterGraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True,
            executor=Executor(),
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

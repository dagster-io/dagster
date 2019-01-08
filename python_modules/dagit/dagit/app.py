from __future__ import absolute_import

import os
import sys

import nbformat
from flask import Flask, send_file, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from flask_sockets import Sockets
from graphql.execution.executors.gevent import GeventExecutor as Executor
from nbconvert import HTMLExporter

from dagster import check
from dagster.cli.dynamic_loader import DynamicObject, load_repository_object_from_target_info

from .pipeline_execution_manager import MultiprocessingExecutionManager, SynchronousExecutionManager
from .schema import create_schema
from .schema.context import DagsterGraphQLContext
from .subscription_server import DagsterSubscriptionServer
from .templates.playground import TEMPLATE as PLAYGROUND_TEMPLATE


class RepositoryContainer(object):
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repository_target_info=None, repository=None):
        if repository_target_info is not None:
            self.repository_target_info = repository_target_info
            self.repo_dynamic_obj = check.inst(
                load_repository_object_from_target_info(repository_target_info), DynamicObject
            )
            self.repo = None
            self.repo_error = None
            self.reload()
        elif repository is not None:
            self.repository_target_info = None
            self.repo = repository
            self.repo_error = None

    def reload(self):
        if not self.repo_dynamic_obj:
            return
        try:
            self.repo = self.repo_dynamic_obj.load()
            self.repo_error = None
        except:  # pylint: disable=W0702
            self.repo_error = sys.exc_info()

    @property
    def repository(self):
        return self.repo

    @property
    def error(self):
        return self.repo_error

    @property
    def repository_info(self):
        return self.repository_target_info


class DagsterGraphQLView(GraphQLView):
    def __init__(self, context, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.context = check.inst_param(context, 'context', DagsterGraphQLContext)

    def get_context(self):
        return self.context


def dagster_graphql_subscription_view(subscription_server, context):
    context = check.inst_param(context, 'context', DagsterGraphQLContext)

    def view(ws):
        subscription_server.handle(ws, request_context=context)
        return []

    return view


def static_view(path, file):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), './webapp/build/static/', path), file
    )


def index_view(_path):
    try:
        return send_file(os.path.join(os.path.dirname(__file__), './webapp/build/index.html'))
    except FileNotFoundError:
        text = '''<p>Can't find webapp files. Probably webapp isn't built. If you are using
        dagit, then probably it's a corrupted installation or a bug. However, if you are
        developing dagit locally, you problem can be fixed as follows:</p>

<pre>cd ./python_modules/
make rebuild_dagit</pre>'''
        return text, 500


def notebook_view(_path):
    # This currently provides open access to your file system - the very least we can
    # do is limit it to notebook files until we create a more permanent solution.
    if not _path.endswith(".ipynb"):
        return "Invalid Path", 400

    with open(os.path.join('/', _path)) as f:
        read_data = f.read()
        notebook = nbformat.reads(read_data, as_version=4)
        html_exporter = HTMLExporter()
        html_exporter.template_file = 'basic'
        (body, resources) = html_exporter.from_notebook_node(notebook)
        return "<style>" + resources['inlining']['css'][0] + "</style>" + body, 200


def create_app(repository_container, pipeline_runs, use_synchronous_execution_manager=False):
    app = Flask('dagster-ui')
    sockets = Sockets(app)
    app.app_protocol = lambda environ_path_info: 'graphql-ws'

    schema = create_schema()
    subscription_server = DagsterSubscriptionServer(schema=schema)

    if use_synchronous_execution_manager:
        execution_manager = SynchronousExecutionManager()
    else:
        execution_manager = MultiprocessingExecutionManager()
    context = DagsterGraphQLContext(
        repository_container=repository_container,
        pipeline_runs=pipeline_runs,
        execution_manager=execution_manager,
    )

    app.add_url_rule(
        '/graphql',
        'graphql',
        DagsterGraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True,
            # XXX(freiksenet): Pass proper ws url
            graphiql_template=PLAYGROUND_TEMPLATE,
            executor=Executor(),
            context=context,
        ),
    )
    sockets.add_url_rule(
        '/graphql', 'graphql', dagster_graphql_subscription_view(subscription_server, context)
    )
    app.add_url_rule('/notebook/<path:_path>', 'notebook', notebook_view)
    app.add_url_rule('/static/<path:path>/<string:file>', 'static_view', static_view)
    app.add_url_rule('/<path:_path>', 'index_catchall', index_view)
    app.add_url_rule('/', 'index', index_view, defaults={'_path': ''})

    CORS(app)

    return app

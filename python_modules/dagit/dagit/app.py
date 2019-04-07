from __future__ import absolute_import

import os
import sys
import subprocess

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote

import nbformat
from flask import Flask, send_file, send_from_directory, request
from flask_cors import CORS
from flask_graphql import GraphQLView
from flask_sockets import Sockets
from graphql.execution.executors.gevent import GeventExecutor as Executor
from nbconvert import HTMLExporter

from dagster import check, RepositoryDefinition, seven
from dagster.cli.dynamic_loader import load_repository_from_target_info
from dagster_graphql.schema import create_schema

from .pipeline_execution_manager import MultiprocessingExecutionManager, SynchronousExecutionManager
from .schema.context import DagsterGraphQLContext
from .subscription_server import DagsterSubscriptionServer
from .templates.playground import TEMPLATE as PLAYGROUND_TEMPLATE
from .version import __version__


class RepositoryContainer(object):
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repository_target_info=None, repository=None):
        self.repo_error = None
        if repository_target_info is not None:
            self.repository_target_info = repository_target_info
            try:
                self.repo = check.inst(
                    load_repository_from_target_info(repository_target_info), RepositoryDefinition
                )
            except:  # pylint: disable=W0702
                self.repo_error = sys.exc_info()
        elif repository is not None:
            self.repository_target_info = None
            self.repo = repository

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
    except seven.FileNotFoundError:
        text = '''<p>Can't find webapp files. Probably webapp isn't built. If you are using
        dagit, then probably it's a corrupted installation or a bug. However, if you are
        developing dagit locally, you problem can be fixed as follows:</p>

<pre>cd ./python_modules/
make rebuild_dagit</pre>'''
        return text, 500


def notebook_view():
    # This currently provides open access to your file system - the very least we can
    # do is limit it to notebook files until we create a more permanent solution.
    path = request.args.get('path')
    if not path.endswith(".ipynb"):
        return "Invalid Path", 400

    with open(os.path.join('/', path)) as f:
        read_data = f.read()
        notebook = nbformat.reads(read_data, as_version=4)
        html_exporter = HTMLExporter()
        html_exporter.template_file = 'basic'
        (body, resources) = html_exporter.from_notebook_node(notebook)
        return "<style>" + resources['inlining']['css'][0] + "</style>" + body, 200


def open_file_view():
    path = request.args.get('path')

    # Jupyter doesn't register as a handler for ipynb files, so calling `open` won't
    # work. Instead, spawn a Jupyter notebook process.
    if path.endswith(".ipynb"):
        subprocess.Popen(['jupyter', 'notebook', path])
        return "Success", 200

    # Fall back to `open` or `xdg-open` for other file types
    if os.name == 'nt':  # For Windows
        os.startfile(path, 'open')  # pylint:disable=no-member
        return "Success", 200

    open_cmd = 'open' if sys.platform.startswith('darwin') else 'xdg-open'
    (exitcode, output) = subprocess.getstatusoutput(open_cmd + ' ' + cmd_quote(path))
    if exitcode == 0:
        return "Success", 200
    else:
        return output, 400


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
        version=__version__,
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

    # these routes are specifically for the Dagit UI and are not part of the graphql
    # API that we want other people to consume, so they're separate for now.
    app.add_url_rule('/dagit/notebook', 'notebook', notebook_view)
    app.add_url_rule('/dagit/open', 'open', open_file_view)

    app.add_url_rule('/static/<path:path>/<string:file>', 'static_view', static_view)
    app.add_url_rule('/<path:_path>', 'index_catchall', index_view)
    app.add_url_rule('/', 'index', index_view, defaults={'_path': ''})

    CORS(app)

    return app

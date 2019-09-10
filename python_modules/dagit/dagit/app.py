from __future__ import absolute_import

import io
import os
import uuid

import nbformat
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import (
    MultiprocessingExecutionManager,
)
from dagster_graphql.schema import create_schema
from flask import Flask, request, send_file, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from flask_sockets import Sockets
from graphql.error.base import GraphQLError
from graphql.execution.executors.gevent import GeventExecutor as Executor
from nbconvert import HTMLExporter
from six import text_type

from dagster import ExecutionTargetHandle, check, seven
from dagster.core.execution.logs import compute_is_complete, get_compute_log_filepath
from dagster.core.instance import DagsterInstance
from dagster.utils.log import get_stack_trace_array

from .subscription_server import DagsterSubscriptionServer
from .templates.playground import TEMPLATE as PLAYGROUND_TEMPLATE
from .version import __version__

try:
    from typing import Any, Dict
except ImportError:
    pass


# based on default_format_error copied and pasted from graphql_server 1.1.1
def format_error_with_stack_trace(error):

    # type: (Exception) -> Dict[str, Any]

    formatted_error = {'message': text_type(error)}  # type: Dict[str, Any]
    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error['locations'] = [
                {'line': loc.line, 'column': loc.column} for loc in error.locations
            ]
        if error.path is not None:
            formatted_error['path'] = error.path

        # this is what is different about this implementation
        # we print out stack traces to ease debugging
        if hasattr(error, 'original_error') and error.original_error:
            formatted_error['stack_trace'] = get_stack_trace_array(error.original_error)

    return formatted_error


class DagsterGraphQLView(GraphQLView):
    def __init__(self, context, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.context = check.inst_param(context, 'context', DagsterGraphQLContext)

    def get_context(self):
        return self.context

    format_error = staticmethod(format_error_with_stack_trace)


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


def vendor_view(path, file):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), './webapp/build/vendor/', path), file
    )


def index_view(_path):
    try:
        return send_file(os.path.join(os.path.dirname(__file__), './webapp/build/index.html'))
    except seven.FileNotFoundError:
        text = '''<p>Can't find webapp files. Probably webapp isn't built. If you are using
        dagit, then probably it's a corrupted installation or a bug. However, if you are
        developing dagit locally, your problem can be fixed as follows:</p>

<pre>cd ./python_modules/
make rebuild_dagit</pre>'''
        return text, 500


def notebook_view(request_args):
    check.dict_param(request_args, 'request_args')

    # This currently provides open access to your file system - the very least we can
    # do is limit it to notebook files until we create a more permanent solution.
    path = request_args['path']
    if not path.endswith('.ipynb'):
        return 'Invalid Path', 400

    with open(os.path.abspath(path)) as f:
        read_data = f.read()
        notebook = nbformat.reads(read_data, as_version=4)
        html_exporter = HTMLExporter()
        html_exporter.template_file = 'basic'
        (body, resources) = html_exporter.from_notebook_node(notebook)
        return '<style>' + resources['inlining']['css'][0] + '</style>' + body, 200


def download_view(context):
    context = check.inst_param(context, 'context', DagsterGraphQLContext)

    def view(run_id, step_key, file_type):
        run_id = str(uuid.UUID(run_id))  # raises if not valid run_id
        step_key = step_key.split('/')[-1]  # make sure we're not diving deep into
        out_name = '{}_{}.{}'.format(run_id, step_key, file_type)
        result = get_compute_log_filepath(context.instance, run_id, step_key, file_type)
        timeout = None if compute_is_complete(context.instance, run_id, step_key) else 0
        if not result:
            result = io.BytesIO()
        return send_file(
            result, as_attachment=True, attachment_filename=out_name, cache_timeout=timeout
        )

    return view


def create_app(handle, instance):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)
    check.inst_param(instance, 'instance', DagsterInstance)

    app = Flask('dagster-ui')
    sockets = Sockets(app)
    app.app_protocol = lambda environ_path_info: 'graphql-ws'

    schema = create_schema()
    subscription_server = DagsterSubscriptionServer(schema=schema)

    execution_manager = MultiprocessingExecutionManager()

    print('Loading repository...')

    context = DagsterGraphQLContext(
        handle=handle, instance=instance, execution_manager=execution_manager, version=__version__
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

    app.add_url_rule(
        # should match the `build_local_download_url`
        '/download/<string:run_id>/<string:step_key>/<string:file_type>',
        'download_view',
        download_view(context),
    )

    # these routes are specifically for the Dagit UI and are not part of the graphql
    # API that we want other people to consume, so they're separate for now.
    # Also grabbing the magic global request args dict so that notebook_view is testable
    app.add_url_rule('/dagit/notebook', 'notebook', lambda: notebook_view(request.args))

    app.add_url_rule('/static/<path:path>/<string:file>', 'static_view', static_view)
    app.add_url_rule('/vendor/<path:path>/<string:file>', 'vendor_view', vendor_view)
    app.add_url_rule('/<path:_path>', 'index_catchall', index_view)
    app.add_url_rule('/', 'index', index_view, defaults={'_path': ''})

    CORS(app)

    return app

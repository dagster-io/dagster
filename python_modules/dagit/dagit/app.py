import gzip
import io
import os
import uuid

import nbformat
from dagster import __version__ as dagster_version
from dagster import check
from dagster.core.debug import DebugRunPayload
from dagster.core.execution.compute_logs import warn_if_compute_logs_disabled
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.telemetry import log_workspace_stats
from dagster.core.workspace.context import IWorkspaceProcessContext, WorkspaceProcessContext
from dagster_graphql.schema import create_schema
from dagster_graphql.version import __version__ as dagster_graphql_version
from flask import Blueprint, Flask, jsonify, redirect, render_template_string, request, send_file
from flask_cors import CORS
from flask_graphql import GraphQLView
from flask_sockets import Sockets
from nbconvert import HTMLExporter

from .format_error import format_error_with_stack_trace
from .subscription_server import DagsterSubscriptionServer
from .templates.playground import TEMPLATE as PLAYGROUND_TEMPLATE
from .version import __version__

MISSING_SCHEDULER_WARNING = (
    "You have defined ScheduleDefinitions for this repository, but have "
    "not defined a scheduler on the instance"
)


class DagsterGraphQLView(GraphQLView):
    def __init__(self, context, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)
        self.context = check.inst_param(context, "context", IWorkspaceProcessContext)

    def get_context(self):
        return self.context.create_request_context()

    format_error = staticmethod(format_error_with_stack_trace)


def dagster_graphql_subscription_view(
    subscription_server: DagsterSubscriptionServer, context: IWorkspaceProcessContext
):
    context = check.inst_param(context, "context", IWorkspaceProcessContext)

    def view(ws):
        # Even though this argument is named as the "request_context", we are passing it
        # a `IWorkspaceProcessContext`. This is a naming restriction from the underlying
        # `GeventSubscriptionServer` which we reply on. If you view the implementation
        # for the DagsterSubscriptionServer, you will see that we create a request context
        # for every GraphQL request in the `on_start` method.
        subscription_server.handle(ws, request_context=context)
        return []

    return view


def info_view():
    return (
        jsonify(
            dagit_version=__version__,
            dagster_graphql_version=dagster_graphql_version,
            dagster_version=dagster_version,
        ),
        200,
    )


def notebook_view(context, request_args):
    context = check.inst_param(context, "context", IWorkspaceProcessContext)
    repo_location_name = request_args["repoLocName"]
    check.dict_param(request_args, "request_args")

    path = request_args["path"]
    if not path.endswith(".ipynb"):
        return "Invalid Path", 400

    # get ipynb content from grpc call
    request_context = context.create_request_context()
    notebook_content = request_context.get_external_notebook_data(repo_location_name, path)
    check.inst_param(notebook_content, "notebook_content", bytes)

    # parse content to HTML
    notebook = nbformat.reads(notebook_content, as_version=4)
    html_exporter = HTMLExporter()
    html_exporter.template_file = "basic"
    (body, resources) = html_exporter.from_notebook_node(notebook)
    return "<style>" + resources["inlining"]["css"][0] + "</style>" + body, 200


def download_log_view(context):
    context = check.inst_param(context, "context", IWorkspaceProcessContext)

    def view(run_id, step_key, file_type):
        run_id = str(uuid.UUID(run_id))  # raises if not valid run_id
        step_key = step_key.split("/")[-1]  # make sure we're not diving deep into
        out_name = f"{run_id}_{step_key}.{file_type}"

        manager = context.instance.compute_log_manager
        try:
            io_type = ComputeIOType(file_type)
            result = manager.get_local_path(run_id, step_key, io_type)
            if not os.path.exists(result):
                result = io.BytesIO()
            timeout = None if manager.is_watch_completed(run_id, step_key) else 0
        except ValueError:
            result = io.BytesIO()
            timeout = 0

        if not result:
            result = io.BytesIO()

        return send_file(
            result, as_attachment=True, attachment_filename=out_name, cache_timeout=timeout
        )

    return view


def download_dump_view(context):
    context = check.inst_param(context, "context", IWorkspaceProcessContext)

    def view(run_id):
        run = context.instance.get_run_by_id(run_id)
        debug_payload = DebugRunPayload.build(context.instance, run)
        check.invariant(run is not None)
        out_name = f"{run_id}.gzip"

        result = io.BytesIO()
        with gzip.GzipFile(fileobj=result, mode="wb") as file:
            debug_payload.write(file)

        result.seek(0)  # be kind, please rewind

        return send_file(result, as_attachment=True, attachment_filename=out_name)

    return view


def instantiate_app_with_views(
    context: IWorkspaceProcessContext,
    schema,
    app_path_prefix,
    target_dir=os.path.dirname(__file__),
    graphql_middleware=None,
    include_notebook_route=False,
):
    app = Flask(
        "dagster-ui",
        static_url_path=app_path_prefix,
        static_folder=os.path.join(target_dir, "./webapp/build"),
    )
    subscription_server = DagsterSubscriptionServer(schema=schema)

    # Websocket routes
    sockets = Sockets(app)
    sockets.add_url_rule(
        f"{app_path_prefix}/graphql",
        "graphql",
        dagster_graphql_subscription_view(subscription_server, context),
    )

    # HTTP routes
    bp = Blueprint("routes", __name__, url_prefix=app_path_prefix)
    bp.add_url_rule("/graphiql", "graphiql", lambda: redirect(f"{app_path_prefix}/graphql", 301))
    bp.add_url_rule(
        "/graphql",
        "graphql",
        DagsterGraphQLView.as_view(
            "graphql",
            schema=schema,
            graphiql=True,
            graphiql_template=PLAYGROUND_TEMPLATE,
            context=context,
            middleware=graphql_middleware,
        ),
    )

    bp.add_url_rule(
        # should match the `build_local_download_url`
        "/download/<string:run_id>/<string:step_key>/<string:file_type>",
        "download_view",
        download_log_view(context),
    )

    bp.add_url_rule(
        "/download_debug/<string:run_id>",
        "download_dump_view",
        download_dump_view(context),
    )

    # these routes are specifically for the Dagit UI and are not part of the graphql
    # API that we want other people to consume, so they're separate for now.
    # Also grabbing the magic global request args dict so that notebook_view is testable
    if include_notebook_route:
        bp.add_url_rule("/dagit/notebook", "notebook", lambda: notebook_view(context, request.args))
    bp.add_url_rule("/dagit_info", "sanity_view", info_view)

    index_path = os.path.join(target_dir, "./webapp/build/index.html")

    def index_view(*args, **kwargs):  # pylint: disable=unused-argument
        try:
            with open(index_path) as f:
                rendered_template = render_template_string(f.read())
                return (
                    rendered_template.replace('href="/', f'href="{app_path_prefix}/')
                    .replace('src="/', f'src="{app_path_prefix}/')
                    .replace("__PATH_PREFIX__", app_path_prefix)
                    .replace("NONCE-PLACEHOLDER", uuid.uuid4().hex)
                )
        except FileNotFoundError:
            raise Exception(
                """Can't find webapp files. Probably webapp isn't built. If you are using
                dagit, then probably it's a corrupted installation or a bug. However, if you are
                developing dagit locally, your problem can be fixed as follows:

                cd ./python_modules/
                make rebuild_dagit"""
            )

    bp.add_url_rule("/", "index_view", index_view)
    bp.add_url_rule("/<path:path>", "catch_all", index_view)

    bp.context_processor(lambda: {"app_path_prefix": app_path_prefix})

    app.app_protocol = lambda environ_path_info: "graphql-ws"
    app.register_blueprint(bp)
    app.register_error_handler(404, index_view)

    CORS(app)

    return app


def create_app_from_workspace_process_context(
    workspace_process_context: WorkspaceProcessContext,
    path_prefix: str = "",
):
    check.inst_param(
        workspace_process_context, "workspace_process_context", WorkspaceProcessContext
    )
    check.str_param(path_prefix, "path_prefix")

    instance = workspace_process_context.instance

    if path_prefix:
        if not path_prefix.startswith("/"):
            raise Exception(f'The path prefix should begin with a leading "/": got {path_prefix}')
        if path_prefix.endswith("/"):
            raise Exception(f'The path prefix should not include a trailing "/": got {path_prefix}')

    warn_if_compute_logs_disabled()

    print("Loading repository...")  # pylint: disable=print-call

    log_workspace_stats(instance, workspace_process_context)

    schema = create_schema()

    return instantiate_app_with_views(
        workspace_process_context, schema, path_prefix, include_notebook_route=True
    )

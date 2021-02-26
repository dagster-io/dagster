from collections import OrderedDict

from graphql_ws.constants import GQL_COMPLETE, GQL_DATA
from graphql_ws.gevent import GeventSubscriptionServer, SubscriptionObserver
from rx import Observable

from .format_error import format_error_with_stack_trace


class DagsterSubscriptionServer(GeventSubscriptionServer):
    """Subscription server that is able to handle non-subscription commands"""

    format_error = staticmethod(format_error_with_stack_trace)

    def __init__(self, middleware=None, **kwargs):
        self.middleware = middleware or []
        super(DagsterSubscriptionServer, self).__init__(**kwargs)

    def execute(self, request_context, params):
        # https://github.com/graphql-python/graphql-ws/issues/7
        params["context_value"] = request_context
        params["middleware"] = self.middleware

        # At this point, `on_start` has already executed and the request_context is
        # actually a WorkspaceRequestContext that contains a snapshot of the data and repository
        # locations for this request.
        return super(DagsterSubscriptionServer, self).execute(request_context, params)

    def send_execution_result(self, connection_context, op_id, execution_result):
        if op_id not in connection_context.operations.keys():
            return

        if execution_result == GQL_COMPLETE:
            return self.send_message(connection_context, op_id, GQL_COMPLETE, {})
        else:
            result = self.execution_result_to_dict(execution_result)
            return self.send_message(connection_context, op_id, GQL_DATA, result)

    def on_start(self, connection_context, op_id, params):
        try:
            execution_result = self.execute(
                # Even though this object is referred to as the "request_context", it is
                # actually a WorkspaceProcessContext. This is a naming restriction from the underlying
                # GeventSubscriptionServer. Here, we create a new request context for every
                # incoming GraphQL request
                connection_context.request_context.create_request_context(),
                params,
            )
            if not isinstance(execution_result, Observable):
                # pylint cannot find of method
                observable = Observable.of(execution_result, GQL_COMPLETE)  # pylint: disable=E1101
                # Register the operation using None even though we are not implementing async
                # iterators. This is useful for bookkeeping purpose, allowing us to ignore generated
                # events for closed operations and avoid sending an unnecessary web socket messages.
                # Requires that `unsubscribe` is overridden to handle the None case.
                connection_context.register_operation(op_id, None)
            else:
                observable = execution_result
                connection_context.register_operation(op_id, observable)

            def on_complete(conn_context):
                # unsubscribe from the completed operation
                self.on_stop(conn_context, op_id)

            observable.subscribe(
                SubscriptionObserver(
                    connection_context,
                    op_id,
                    self.send_execution_result,
                    self.send_error,
                    on_complete,
                )
            )

        # appropriate to catch all errors here
        except Exception as e:  # pylint: disable=W0703
            self.send_error(connection_context, op_id, str(e))

    def unsubscribe(self, connection_context, op_id):
        if connection_context.has_operation(op_id):
            operation = connection_context.get_operation(op_id)
            if not operation:
                # there is no operation, we are just using the connection context for bookkeeping
                pass
            elif callable(getattr(operation, "dispose", None)):
                # handle the generic async iterator case
                operation.dispose()
            connection_context.remove_operation(op_id)
        self.on_operation_complete(connection_context, op_id)

    # overrides graphql_ws.base.BaseSubscriptionServer.execution_result_to_dict because, unlike
    # the implementation in GraphQLView, format_error is not pluggable (cf.
    # dagit.app.DagsterGraphQLView)
    def execution_result_to_dict(self, execution_result):
        result = OrderedDict()
        if execution_result.data:
            result["data"] = execution_result.data
        if execution_result.errors:
            result["errors"] = [self.format_error(error) for error in execution_result.errors]
        return result

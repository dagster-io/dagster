from rx import Observable
from graphql_ws.constants import GQL_DATA, GQL_COMPLETE
from graphql_ws.gevent import GeventSubscriptionServer, SubscriptionObserver


class DagsterSubscriptionServer(GeventSubscriptionServer):
    '''Subscription server that is able to handle non-subscription commands'''

    def __init__(self, middleware=None, **kwargs):
        self.middleware = middleware or []
        super(DagsterSubscriptionServer, self).__init__(**kwargs)

    def execute(self, request_context, params):
        # https://github.com/graphql-python/graphql-ws/issues/7
        params['context_value'] = request_context
        params['middleware'] = self.middleware
        return super(DagsterSubscriptionServer, self).execute(request_context, params)

    def send_execution_result(self, connection_context, op_id, execution_result):
        if execution_result == GQL_COMPLETE:
            return self.send_message(connection_context, op_id, GQL_COMPLETE, {})
        else:
            result = self.execution_result_to_dict(execution_result)
            return self.send_message(connection_context, op_id, GQL_DATA, result)

    def on_start(self, connection_context, op_id, params):
        try:
            execution_result = self.execute(connection_context.request_context, params)
            if not isinstance(execution_result, Observable):
                # pylint cannot find of method
                observable = Observable.of(execution_result, GQL_COMPLETE)  # pylint: disable=E1101
            else:
                observable = execution_result
            observable.subscribe(
                SubscriptionObserver(
                    connection_context,
                    op_id,
                    self.send_execution_result,
                    self.send_error,
                    self.on_close,
                )
            )
        # appropriate to catch all errors here
        except Exception as e:  # pylint: disable=W0703
            self.send_error(connection_context, op_id, str(e))

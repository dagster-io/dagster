from graphql import graphql

from dagster_graphql.schema import create_schema


def execute_dagster_graphql(context, query, variables=None):
    result = graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        # executor=GeventObservableExecutor(),
        allow_subscriptions=True,
        return_promise=False,
    )

    # has to check attr because in subscription case it returns AnonymousObservable
    if hasattr(result, 'errors') and result.errors:
        first_error = result.errors[0]
        if hasattr(first_error, 'original_error') and first_error.original_error:
            raise result.errors[0].original_error

        raise result.errors[0]

    return result

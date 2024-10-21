import {ApolloLink} from '../apollo-client';
import {appendApolloQueryParams} from './appendApolloQueryParams';

// Add the `op` as a query param to the request URL.
export const createOperationQueryStringApolloLink = (basePath: string) =>
  new ApolloLink((operation, forward) => {
    const {operationName} = operation;
    if (operationName) {
      const name = encodeURIComponent(operationName);

      // If a `uri` value has been provided by a previous link in the chain, use it.
      // Otherwise use the `basePath` value.
      const {uri = `${basePath}/graphql`} = operation.getContext();
      operation.setContext({
        ...operation.getContext(),
        uri: appendApolloQueryParams(uri, {op: name}),
      });
    }

    return forward(operation);
  });

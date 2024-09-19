import {ApolloLink} from '../apollo-client';

export const createOperationQueryStringApolloLink = (basePath: string) =>
  new ApolloLink((operation, forward) => {
    const {operationName} = operation;
    if (operationName) {
      const name = encodeURIComponent(operationName);
      operation.setContext({
        ...operation.getContext(),
        uri: `${basePath}/graphql?op=${name}`,
      });
    }

    return forward(operation);
  });

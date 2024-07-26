import {ApolloLink, Observable} from '@apollo/client';

export const createOperationQueryStringApolloLink = (basePath: string) =>
  new ApolloLink((operation, forward) => {
    return new Observable((observer) => {
      const {operationName} = operation;
      if (operationName) {
        const name = encodeURIComponent(operationName);
        operation.setContext({
          ...operation.getContext(),
          uri: `${basePath}/graphql?op=${name}`,
        });
      }

      const subscriber = {
        next: observer.next.bind(observer),
        error: observer.error.bind(observer),
        complete: observer.complete.bind(observer),
      };

      // Continue the request chain
      forward(operation).subscribe(subscriber);
    });
  });

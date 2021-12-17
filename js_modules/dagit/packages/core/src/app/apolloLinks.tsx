import {ApolloLink} from '@apollo/client';

import {formatElapsedTime, debugLog} from './Util';

export const logLink = new ApolloLink((operation, forward) =>
  forward(operation).map((data) => {
    const context = operation.getContext();
    const elapsedTime = performance.now() - context.start;
    const calls = JSON.parse(context.response.headers.get('x-dagster-call-counts'));
    operation.setContext({elapsedTime, calls});
    debugLog(`${operation.operationName} took ${formatElapsedTime(elapsedTime)}`, {
      operation,
      data,
      calls,
    });
    return data;
  }),
);

export const timeStartLink = new ApolloLink((operation, forward) => {
  operation.setContext({start: performance.now()});
  return forward(operation);
});

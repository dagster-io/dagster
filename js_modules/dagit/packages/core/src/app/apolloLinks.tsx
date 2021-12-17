import {ApolloLink} from '@apollo/client';

import {formatElapsedTime, debugLog} from './Util';

export const getCalls = (response: any) => {
  try {
    return JSON.parse(response.headers.get('x-dagster-call-counts'));
  } catch {
    return null;
  }
};

export const logLink = new ApolloLink((operation, forward) =>
  forward(operation).map((data) => {
    const context = operation.getContext();
    const elapsedTime = performance.now() - context.start;
    const calls = getCalls(context.response);
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

import {ApolloLink} from '@apollo/client';

import {formatElapsedTime, debugLog} from './Util';

export const logLink = new ApolloLink((operation, forward) =>
  forward(operation).map((data) => {
    const time = performance.now() - operation.getContext().start;
    operation.setContext({elapsedTime: time});
    debugLog(`${operation.operationName} took ${formatElapsedTime(time)}`, {operation, data});
    return data;
  }),
);

export const timeStartLink = new ApolloLink((operation, forward) => {
  operation.setContext({start: performance.now()});
  return forward(operation);
});

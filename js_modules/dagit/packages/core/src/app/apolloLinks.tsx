import {ApolloLink} from '@apollo/client';

import {TelemetryAction, logTelemetry} from './Telemetry';
import {formatElapsedTime, debugLog} from './Util';

const TELEMETRY_WHITELIST = new Set(['PipelineRunsRootQuery']);

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

export const logTelemetryLink = new ApolloLink((operation, forward) =>
  forward(operation).map((data) => {
    if (TELEMETRY_WHITELIST.has(operation.operationName)) {
      const elapsedTime = operation.getContext().elapsedTime;
      logTelemetry(TelemetryAction.GRAPHQL_QUERY_COMPLETED, {
        operationName: operation.operationName,
        elapsedTime: elapsedTime.toString(),
      });
    }
    return data;
  }),
);

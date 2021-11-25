import {ApolloLink} from '@apollo/client';

import {TelemetryAction, useTelemetryAction} from './Telemetry';

import {formatElapsedTime, debugLog} from './Util';

const TELEMETRY_WHITELIST = new Set(['PipelineRunsRootQuery']);

export const logLink = new ApolloLink((operation, forward) =>
  forward(operation).map((data) => {
    const logQueryCompletion = useTelemetryAction(TelemetryAction.GRAPHQL_QUERY_COMPLETED);
    const time = performance.now() - operation.getContext().start;
    debugLog(`${operation.operationName} took ${formatElapsedTime(time)}`, {operation, data});
    if (TELEMETRY_WHITELIST.has(operation.operationName)) {
      logQueryCompletion({operationName: operation.operationName, elapsedTime: time.toString()});
    }
    return data;
  }),
);

export const timeStartLink = new ApolloLink((operation, forward) => {
  operation.setContext({start: performance.now()});
  return forward(operation);
});

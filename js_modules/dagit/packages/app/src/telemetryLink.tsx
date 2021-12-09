import {ApolloLink} from '@apollo/client';
import {TelemetryAction, logTelemetry} from '@dagit/core/app/Telemetry';

const TELEMETRY_WHITELIST = new Set(['PipelineRunsRootQuery']);

export const telemetryLink = (pathPrefix: string) => {
  return new ApolloLink((operation, forward) =>
    forward(operation).map((data) => {
      if (TELEMETRY_WHITELIST.has(operation.operationName)) {
        const elapsedTime = operation.getContext().elapsedTime;
        logTelemetry(pathPrefix, TelemetryAction.GRAPHQL_QUERY_COMPLETED, {
          operationName: operation.operationName,
          elapsedTime: elapsedTime.toString(),
        });
      }
      return data;
    }),
  );
};

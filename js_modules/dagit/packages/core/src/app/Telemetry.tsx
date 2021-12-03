import {gql} from '@apollo/client';
import {extractInitializationData} from '@dagit/app/src/extractInitializationData';
import {print} from 'graphql';

export enum TelemetryAction {
  LAUNCH_RUN = 'LAUNCH_RUN',
  GRAPHQL_QUERY_COMPLETED = 'GRAPHQL_QUERY_COMPLETED',
}

const initializationData = extractInitializationData();
const {pathPrefix, telemetryEnabled} = initializationData;

const GRAPHQL_PATH = `${pathPrefix || ''}/graphql`;

const LOG_TELEMETRY_MUTATION = gql`
  mutation LogTelemetryMutation($action: String!, $metadata: String!, $clientTime: String!) {
    logTelemetry(action: $action, metadata: $metadata, clientTime: $clientTime) {
      ... on LogTelemetrySuccess {
        action
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export async function logTelemetry(
  action: TelemetryAction,
  metadata: {[key: string]: string | null | undefined} = {},
) {
  if (telemetryEnabled) {
    return;
  }
  return fetch(GRAPHQL_PATH, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      query: print(LOG_TELEMETRY_MUTATION),
      variables: {
        action,
        metadata: JSON.stringify(metadata),
        clientTime: Date.now(),
      },
    }),
  });
}

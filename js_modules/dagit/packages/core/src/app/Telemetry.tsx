import {gql} from '@apollo/client';
import {extractPathPrefix} from '@dagit/app/src/extractPathPrefix';
import {print} from 'graphql';

import {DagitTelemetryEnabledQuery} from './types/DagitTelemetryEnabledQuery';

export enum TelemetryAction {
  LAUNCH_RUN = 'LAUNCH_RUN',
  GRAPHQL_QUERY_COMPLETED = 'GRAPHQL_QUERY_COMPLETED',
}

const TELEMETRY_ENABLED_QUERY = gql`
  query DagitTelemetryEnabledQuery {
    instance {
      dagitTelemetryEnabled
    }
  }
`;

const GRAPHQL_PATH = `${extractPathPrefix() || ''}/graphql`;

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

let __DAGIT_TELEMETRY_FLAG: boolean | undefined = undefined;

export async function logTelemetry(
  action: TelemetryAction,
  metadata: {[key: string]: string | null | undefined} = {},
) {
  if (__DAGIT_TELEMETRY_FLAG === undefined) {
    const enabledResponse = await fetch(GRAPHQL_PATH, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        query: print(TELEMETRY_ENABLED_QUERY),
      }),
    });
    const payload = (await enabledResponse.json()) as {data: DagitTelemetryEnabledQuery};
    const data = payload.data;
    __DAGIT_TELEMETRY_FLAG = data.instance.dagitTelemetryEnabled;
  }
  if (!__DAGIT_TELEMETRY_FLAG) {
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

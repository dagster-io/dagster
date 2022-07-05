import {gql} from '@apollo/client';
import {print} from 'graphql';
import * as React from 'react';

import {AppContext} from './AppContext';
import {PYTHON_ERROR_FRAGMENT} from './PythonErrorFragment';

export enum TelemetryAction {
  LAUNCH_RUN = 'LAUNCH_RUN',
  GRAPHQL_QUERY_COMPLETED = 'GRAPHQL_QUERY_COMPLETED',
}

const LOG_TELEMETRY_MUTATION = gql`
  mutation LogTelemetryMutation($action: String!, $metadata: String!, $clientTime: String!) {
    logTelemetry(action: $action, metadata: $metadata, clientTime: $clientTime) {
      ... on LogTelemetrySuccess {
        action
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export async function logTelemetry(
  pathPrefix: string,
  action: TelemetryAction,
  metadata: {[key: string]: string | null | undefined} = {},
) {
  const graphqlPath = `${pathPrefix || ''}/graphql`;

  return fetch(graphqlPath, {
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

export const useTelemetryAction = () => {
  const {basePath, telemetryEnabled} = React.useContext(AppContext);
  return React.useCallback(
    (action: TelemetryAction, metadata: {[key: string]: string | null | undefined} = {}) => {
      if (telemetryEnabled) {
        logTelemetry(basePath, action, metadata);
      }
    },
    [basePath, telemetryEnabled],
  );
};

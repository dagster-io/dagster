import {gql} from '@apollo/client';
import {print} from 'graphql';
import memoize from 'lodash/memoize';
import * as React from 'react';
import {v4 as uuidv4} from 'uuid';

import {AppContext} from './AppContext';
import {PYTHON_ERROR_FRAGMENT} from './PythonErrorFragment';

export enum TelemetryAction {
  LAUNCH_RUN = 'LAUNCH_RUN',
  GRAPHQL_QUERY_COMPLETED = 'GRAPHQL_QUERY_COMPLETED',
}

const LOG_TELEMETRY_MUTATION = gql`
  mutation LogTelemetryMutation(
    $action: String!
    $metadata: String!
    $clientTime: String!
    $clientId: String!
  ) {
    logTelemetry(
      action: $action
      metadata: $metadata
      clientTime: $clientTime
      clientId: $clientId
    ) {
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
        clientTime: String(Date.now()),
        clientId: clientID(),
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

const TELEMETRY_CLIENT_ID_KEY = 'dagit.telemetry_client_id';
const clientID = memoize(() => {
  let retrievedClientID = window.localStorage.getItem(TELEMETRY_CLIENT_ID_KEY);
  if (retrievedClientID === null) {
    retrievedClientID = uuidv4();
    window.localStorage.setItem(TELEMETRY_CLIENT_ID_KEY, retrievedClientID);
  }
  return retrievedClientID;
});

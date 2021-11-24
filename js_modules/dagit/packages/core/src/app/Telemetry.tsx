import {gql, useMutation, useQuery} from '@apollo/client';

import {DagitTelemetryEnabledQuery} from './types/DagitTelemetryEnabledQuery';

export enum TelemetryAction {
  LAUNCH_RUN = 'LAUNCH_RUN',
}

const TELEMETRY_ENABLED_QUERY = gql`
  query DagitTelemetryEnabledQuery {
    instance {
      dagitTelemetryEnabled
    }
  }
`;

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

export const useTelemetryAction = (action: TelemetryAction) => {
  const [telemetryRequest] = useMutation(LOG_TELEMETRY_MUTATION);
  const {data} = useQuery<DagitTelemetryEnabledQuery>(TELEMETRY_ENABLED_QUERY);

  return (metadata: {[key: string]: string | null | undefined} = {}) => {
    if (data && data.instance.dagitTelemetryEnabled) {
      telemetryRequest({
        variables: {
          action: action.toString(),
          metadata: JSON.stringify(metadata),
          clientTime: Date.now(),
        },
      });
    }
  };
};

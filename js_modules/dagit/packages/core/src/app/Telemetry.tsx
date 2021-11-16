import {gql, useMutation} from '@apollo/client';

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

export const useTelemetryAction = (action: string, metadata: {[key: string]: string}={}) => {
    const clientTime = Date.now()
    const metadataString = JSON.stringify(metadata)
    const telemetryRequest = useMutation(LOG_TELEMETRY_MUTATION, {
        variables: {action: action, metadata: metadataString, clientTime: clientTime},
      });

    const [loggedAction] = telemetryRequest;
    return loggedAction;
}
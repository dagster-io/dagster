import {gql, useMutation} from '@apollo/client';


export enum TelemetryAction {
  LAUNCH_RUN="LAUNCH_RUN",
}

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

export const useTelemetryAction = (action: TelemetryAction, metadata: {[key: string]: string | null | undefined}={}) => {
    const clientTime = Date.now()
    const metadataString = JSON.stringify(metadata)
    const telemetryRequest = useMutation(LOG_TELEMETRY_MUTATION, {
        variables: {action: action.toString(), metadata: metadataString, clientTime: clientTime},
      });

    const [loggedAction] = telemetryRequest;
    return loggedAction;
}
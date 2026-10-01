import {gql} from '../apollo-client';

// Refresh state for a single state-backed component. The resolver waits
// synchronously for a bounded window: Success means the gRPC refresh finished
// (and the code location has been reloaded in place); Error means the refresh
// completed but failed; Accepted means the wait window elapsed first, and the
// frontend should poll componentsForLocation until the version on the key
// changes from its captured original.
export const REFRESH_COMPONENT_STATE_MUTATION = gql`
  mutation RefreshComponentStateMutation($locationName: String!, $defsStateKey: String!) {
    refreshComponentState(locationName: $locationName, defsStateKey: $defsStateKey) {
      __typename
      ... on RefreshComponentStateSuccess {
        component {
          componentId
          componentType
          isAppManaged
          defsStateKey
          defsStateInfo {
            version
            createTimestamp
            managementType
          }
        }
      }
      ... on RefreshComponentStateAccepted {
        locationName
        defsStateKey
      }
      ... on RefreshComponentStateError {
        locationName
        defsStateKey
        message
      }
      ... on UnauthorizedError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
`;

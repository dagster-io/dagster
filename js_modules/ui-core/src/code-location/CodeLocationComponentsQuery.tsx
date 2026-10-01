import {gql} from '../apollo-client';

// Unified query covering both file-based and app-managed components. The
// resolver pulls leaves from the repository snapshot's component_tree and
// layers in YAML attributes from defs state storage for app-managed entries.
export const CODE_LOCATION_COMPONENTS_QUERY = gql`
  query CodeLocationComponentsQuery($locationName: String!) {
    componentsForLocationOrError(locationName: $locationName) {
      __typename
      ... on Components {
        locationName
        components {
          componentId
          componentType
          isAppManaged
          attributes
          defsStateKey
          defsStateManagementType
          defsStateInfo {
            version
            createTimestamp
            managementType
          }
        }
      }
      ... on PythonError {
        message
      }
    }
  }
`;

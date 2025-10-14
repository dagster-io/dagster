import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const CODE_LOCATION_DEFS_STATE_QUERY = gql`
  query CodeLocationDefsStateQuery($locationName: String!) {
    latestDefsStateInfo {
      keyStateInfo {
        name
        info {
          version
          createTimestamp
          managementType
        }
      }
    }
    workspaceLocationEntryOrError(name: $locationName) {
      ... on WorkspaceLocationEntry {
        id
        defsStateInfo {
          keyStateInfo {
            name
            info {
              version
              createTimestamp
              managementType
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

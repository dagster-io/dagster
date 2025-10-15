import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const DEFS_STATE_INFO_FRAGMENT = gql`
  fragment DefsStateInfoFragment on DefsStateInfo {
    keyStateInfo {
      name
      info {
        version
        createTimestamp
      }
    }
  }
`;

export const CODE_LOCATION_DEFS_STATE_QUERY = gql`
  query CodeLocationDefsStateQuery($locationName: String!) {
    latestDefsStateInfo {
      ...DefsStateInfoFragment
    }
    workspaceLocationEntryOrError(name: $locationName) {
      ... on WorkspaceLocationEntry {
        id
        defsStateInfo {
          ...DefsStateInfoFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${DEFS_STATE_INFO_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

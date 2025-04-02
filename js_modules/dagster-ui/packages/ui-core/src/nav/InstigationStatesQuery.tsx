import {gql} from '../apollo-client';
import {INSTIGATION_STATE_BASE_FRAGMENT} from '../instigation/InstigationStateBaseFragment';

export const INSTIGATION_STATES_QUERY = gql`
  query InstigationStatesQuery($repositoryID: String!) {
    instigationStatesOrError(repositoryID: $repositoryID) {
      ... on PythonError {
        message
        stack
      }
      ... on InstigationStates {
        results {
          id
          ...InstigationStateBaseFragment
        }
      }
    }
  }
  ${INSTIGATION_STATE_BASE_FRAGMENT}
`;

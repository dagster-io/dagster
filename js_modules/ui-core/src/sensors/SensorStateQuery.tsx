import {gql} from '../apollo-client';
import {INSTIGATION_STATE_BASE_FRAGMENT} from '../instigation/InstigationStateBaseFragment';

export const SENSOR_STATE_QUERY = gql`
  query SensorStateQuery($id: String!, $selector: InstigationSelector!) {
    instigationStateOrError(id: $id, instigationSelector: $selector) {
      ... on InstigationState {
        id
        ...InstigationStateBaseFragment
      }
    }
  }
  ${INSTIGATION_STATE_BASE_FRAGMENT}
`;

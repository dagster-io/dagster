import {gql} from '../apollo-client';

export const INSTIGATION_STATE_BASE_FRAGMENT = gql`
  fragment InstigationStateBaseFragment on InstigationState {
    id
    selectorId
    name
    instigationType
    status
    runningCount
  }
`;

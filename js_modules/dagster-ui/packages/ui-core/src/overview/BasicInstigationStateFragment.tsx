import {gql} from '@apollo/client';

export const BASIC_INSTIGATION_STATE_FRAGMENT = gql`
  fragment BasicInstigationStateFragment on InstigationState {
    id
    selectorId
    status
    hasStartPermission
    hasStopPermission
  }
`;

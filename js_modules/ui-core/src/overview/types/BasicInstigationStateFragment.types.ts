// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type BasicInstigationStateFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  status: Types.InstigationStatus;
  hasStartPermission: boolean;
  hasStopPermission: boolean;
};

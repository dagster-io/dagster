/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type BasicInstigationStateFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  status: Types.InstigationStatus;
  hasStartPermission: boolean;
  hasStopPermission: boolean;
};

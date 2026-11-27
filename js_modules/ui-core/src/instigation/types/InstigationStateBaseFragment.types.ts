/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

export type InstigationStateBaseFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  name: string;
  instigationType: Types.InstigationType;
  status: Types.InstigationStatus;
  runningCount: number;
};

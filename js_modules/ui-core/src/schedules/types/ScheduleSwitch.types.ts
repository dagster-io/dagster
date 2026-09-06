/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationSelector = {
  name: string;
  repositoryLocationName: string;
  repositoryName: string;
};

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

export type ScheduleStateQueryVariables = Exact<{
  id: string;
  selector: Types.InstigationSelector;
}>;

export type ScheduleStateQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        selectorId: string;
        name: string;
        instigationType: Types.InstigationType;
        status: Types.InstigationStatus;
        runningCount: number;
      }
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};

export const ScheduleStateQueryVersion = '75bc752d4f1df0fc2829736c14a4c2f707981571eb83a9139fa7048d202b3491';

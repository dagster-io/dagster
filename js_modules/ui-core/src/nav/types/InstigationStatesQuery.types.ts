/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

export type InstigationStatesQueryVariables = Exact<{
  repositoryID: string;
}>;

export type InstigationStatesQuery = {
  __typename: 'Query';
  instigationStatesOrError:
    | {
        __typename: 'InstigationStates';
        results: Array<{
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
          runningCount: number;
        }>;
      }
    | {__typename: 'PythonError'; message: string; stack: Array<string>};
};

export const InstigationStatesQueryVersion = '98c41676dfb3c489e46455a3c2716e375050c9bed2d73e74c765453f2c63d0da';

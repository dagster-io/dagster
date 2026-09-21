/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type ScheduleSelector = {
  repositoryLocationName: string;
  repositoryName: string;
  scheduleName: string;
};

export type SchedulePartitionStatusQueryVariables = Exact<{
  scheduleSelector: Types.ScheduleSelector;
}>;

export type SchedulePartitionStatusQuery = {
  __typename: 'Query';
  scheduleOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Schedule';
        id: string;
        mode: string;
        pipelineName: string;
        partitionSet: {
          __typename: 'PartitionSet';
          id: string;
          name: string;
          partitionStatusesOrError:
            | {
                __typename: 'PartitionStatuses';
                results: Array<{
                  __typename: 'PartitionStatus';
                  id: string;
                  partitionName: string;
                  runStatus: Types.RunStatus | null;
                }>;
              }
            | {__typename: 'PythonError'};
        } | null;
      }
    | {__typename: 'ScheduleNotFoundError'};
};

export type SchedulePartitionStatusFragment = {
  __typename: 'Schedule';
  id: string;
  mode: string;
  pipelineName: string;
  partitionSet: {
    __typename: 'PartitionSet';
    id: string;
    name: string;
    partitionStatusesOrError:
      | {
          __typename: 'PartitionStatuses';
          results: Array<{
            __typename: 'PartitionStatus';
            id: string;
            partitionName: string;
            runStatus: Types.RunStatus | null;
          }>;
        }
      | {__typename: 'PythonError'};
  } | null;
};

export type SchedulePartitionStatusResultFragment = {
  __typename: 'PartitionStatus';
  id: string;
  partitionName: string;
  runStatus: Types.RunStatus | null;
};

export const SchedulePartitionStatusQueryVersion = 'f5440153ccc2480dfdd8c6a7e9371c7276d1d27016e3820c0ba1488523e55d5b';

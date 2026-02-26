// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SchedulePartitionStatusQueryVariables = Types.Exact<{
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

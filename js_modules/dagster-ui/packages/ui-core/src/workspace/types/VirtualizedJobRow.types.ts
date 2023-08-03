// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleJobQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
}>;

export type SingleJobQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        name: string;
        isJob: boolean;
        description: string | null;
        runs: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
        }>;
        schedules: Array<{
          __typename: 'Schedule';
          id: string;
          name: string;
          cronSchedule: string;
          executionTimezone: string | null;
          scheduleState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
          };
        }>;
        sensors: Array<{
          __typename: 'Sensor';
          id: string;
          jobOriginId: string;
          name: string;
          sensorState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
          };
        }>;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

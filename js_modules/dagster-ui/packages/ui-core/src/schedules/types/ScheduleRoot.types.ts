// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduleRootQueryVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
}>;

export type ScheduleRootQuery = {
  __typename: 'Query';
  scheduleOrError:
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'Schedule';
        id: string;
        name: string;
        cronSchedule: string;
        executionTimezone: string | null;
        pipelineName: string;
        solidSelection: Array<string | null> | null;
        mode: string;
        description: string | null;
        defaultStatus: Types.InstigationStatus;
        canReset: boolean;
        partitionSet: {__typename: 'PartitionSet'; id: string; name: string} | null;
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
          hasStartPermission: boolean;
          hasStopPermission: boolean;
          repositoryName: string;
          repositoryLocationName: string;
          runningCount: number;
          typeSpecificData:
            | {__typename: 'ScheduleData'; cronSchedule: string}
            | {__typename: 'SensorData'; lastRunKey: string | null; lastCursor: string | null}
            | null;
          runs: Array<{
            __typename: 'Run';
            id: string;
            status: Types.RunStatus;
            creationTime: number;
            startTime: number | null;
            endTime: number | null;
            updateTime: number | null;
          }>;
          ticks: Array<{
            __typename: 'InstigationTick';
            id: string;
            cursor: string | null;
            status: Types.InstigationTickStatus;
            timestamp: number;
            skipReason: string | null;
            runIds: Array<string>;
            runKeys: Array<string>;
            error: {
              __typename: 'PythonError';
              message: string;
              stack: Array<string>;
              errorChain: Array<{
                __typename: 'ErrorChainLink';
                isExplicitLink: boolean;
                error: {__typename: 'PythonError'; message: string; stack: Array<string>};
              }>;
            } | null;
          }>;
        };
        futureTicks: {
          __typename: 'DryRunInstigationTicks';
          results: Array<{__typename: 'DryRunInstigationTick'; timestamp: number | null}>;
        };
      }
    | {__typename: 'ScheduleNotFoundError'; message: string};
  instance: {
    __typename: 'Instance';
    id: string;
    hasInfo: boolean;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {__typename: 'DaemonStatus'; id: string; healthy: boolean | null};
      allDaemonStatuses: Array<{
        __typename: 'DaemonStatus';
        id: string;
        daemonType: string;
        required: boolean;
        healthy: boolean | null;
        lastHeartbeatTime: number | null;
        lastHeartbeatErrors: Array<{
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        }>;
      }>;
    };
  };
};

export const ScheduleRootQueryVersion = 'b54dfb64f816baa5c52c4676dcbd3808477130cab5237a5b96b988ec002adafc';

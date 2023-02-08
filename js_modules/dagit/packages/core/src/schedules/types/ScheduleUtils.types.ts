// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduleFragment = {
  __typename: 'Schedule';
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: Array<string | null> | null;
  mode: string;
  description: string | null;
  partitionSet: {__typename: 'PartitionSet'; id: string; name: string} | null;
  scheduleState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    name: string;
    instigationType: Types.InstigationType;
    status: Types.InstigationStatus;
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
      runId: string;
      status: Types.RunStatus;
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
};

export type RepositorySchedulesFragment = {
  __typename: 'Repository';
  name: string;
  id: string;
  location: {__typename: 'RepositoryLocation'; id: string; name: string};
  schedules: Array<{
    __typename: 'Schedule';
    id: string;
    name: string;
    cronSchedule: string;
    executionTimezone: string | null;
    pipelineName: string;
    solidSelection: Array<string | null> | null;
    mode: string;
    description: string | null;
    partitionSet: {__typename: 'PartitionSet'; id: string; name: string} | null;
    scheduleState: {
      __typename: 'InstigationState';
      id: string;
      selectorId: string;
      name: string;
      instigationType: Types.InstigationType;
      status: Types.InstigationStatus;
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
        runId: string;
        status: Types.RunStatus;
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
  }>;
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
};

export type SchedulesRootQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
  instigationType: Types.InstigationType;
}>;

export type SchedulesRootQuery = {
  __typename: 'DagitQuery';
  repositoryOrError:
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
        __typename: 'Repository';
        id: string;
        name: string;
        location: {__typename: 'RepositoryLocation'; id: string; name: string};
        schedules: Array<{
          __typename: 'Schedule';
          id: string;
          name: string;
          cronSchedule: string;
          executionTimezone: string | null;
          pipelineName: string;
          solidSelection: Array<string | null> | null;
          mode: string;
          description: string | null;
          partitionSet: {__typename: 'PartitionSet'; id: string; name: string} | null;
          scheduleState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            name: string;
            instigationType: Types.InstigationType;
            status: Types.InstigationStatus;
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
              runId: string;
              status: Types.RunStatus;
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
        }>;
        displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
      }
    | {__typename: 'RepositoryNotFoundError'};
  unloadableInstigationStatesOrError:
    | {
        __typename: 'InstigationStates';
        results: Array<{
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
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
            runId: string;
            status: Types.RunStatus;
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
        }>;
      }
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
  instance: {
    __typename: 'Instance';
    hasInfo: boolean;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
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

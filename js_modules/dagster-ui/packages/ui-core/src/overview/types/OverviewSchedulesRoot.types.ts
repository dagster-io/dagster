// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OverviewSchedulesQueryVariables = Types.Exact<{[key: string]: never}>;

export type OverviewSchedulesQuery = {
  __typename: 'Query';
  workspaceOrError:
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
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          locationOrLoadError:
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
                __typename: 'RepositoryLocation';
                id: string;
                name: string;
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  name: string;
                  schedules: Array<{
                    __typename: 'Schedule';
                    id: string;
                    name: string;
                    description: string | null;
                    scheduleState: {
                      __typename: 'InstigationState';
                      id: string;
                      selectorId: string;
                      status: Types.InstigationStatus;
                      hasStartPermission: boolean;
                      hasStopPermission: boolean;
                    };
                  }>;
                }>;
              }
            | null;
        }>;
      };
  unloadableInstigationStatesOrError:
    | {
        __typename: 'InstigationStates';
        results: Array<{__typename: 'InstigationState'; id: string}>;
      }
    | {__typename: 'PythonError'};
  instance: {
    __typename: 'Instance';
    id: string;
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

export type UnloadableSchedulesQueryVariables = Types.Exact<{[key: string]: never}>;

export type UnloadableSchedulesQuery = {
  __typename: 'Query';
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
};

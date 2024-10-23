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

export const OverviewSchedulesQueryVersion = '04a2e4a6537d8d9de9aecfb08bb82bebf73767cf1858b3eddd0c063779129c39';

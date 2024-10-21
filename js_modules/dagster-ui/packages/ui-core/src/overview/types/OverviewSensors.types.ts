// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OverviewSensorsQueryVariables = Types.Exact<{[key: string]: never}>;

export type OverviewSensorsQuery = {
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
                  sensors: Array<{
                    __typename: 'Sensor';
                    id: string;
                    name: string;
                    description: string | null;
                    sensorType: Types.SensorType;
                    sensorState: {
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

export const OverviewSensorsQueryVersion = 'a4165ae0c5e53e870380e53b7cab308203a28d002f81f0d5e4e767c7d91a3029';

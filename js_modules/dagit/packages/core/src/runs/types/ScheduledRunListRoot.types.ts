// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduledRunsListQueryVariables = Types.Exact<{[key: string]: never}>;

export type ScheduledRunsListQuery = {
  __typename: 'Query';
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
  repositoriesOrError:
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
        __typename: 'RepositoryConnection';
        nodes: Array<{
          __typename: 'Repository';
          id: string;
          name: string;
          location: {__typename: 'RepositoryLocation'; id: string; name: string};
          schedules: Array<{
            __typename: 'Schedule';
            id: string;
            name: string;
            executionTimezone: string | null;
            mode: string;
            solidSelection: Array<string | null> | null;
            pipelineName: string;
            scheduleState: {
              __typename: 'InstigationState';
              id: string;
              status: Types.InstigationStatus;
            };
            futureTicks: {
              __typename: 'DryRunInstigationTicks';
              results: Array<{__typename: 'DryRunInstigationTick'; timestamp: number | null}>;
            };
          }>;
        }>;
      };
};

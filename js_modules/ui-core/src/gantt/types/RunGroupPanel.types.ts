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

export type RunGroupPanelQueryVariables = Exact<{
  runId: string;
}>;

export type RunGroupPanelQuery = {
  __typename: 'Query';
  runGroupOrError:
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
        __typename: 'RunGroup';
        rootRunId: string;
        runs: Array<{
          __typename: 'Run';
          id: string;
          parentRunId: string | null;
          status: Types.RunStatus;
          stepKeysToExecute: Array<string> | null;
          pipelineName: string;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        } | null> | null;
      }
    | {__typename: 'RunGroupNotFoundError'};
};

export type RunGroupPanelRunFragment = {
  __typename: 'Run';
  id: string;
  parentRunId: string | null;
  status: Types.RunStatus;
  stepKeysToExecute: Array<string> | null;
  pipelineName: string;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export const RunGroupPanelQueryVersion = 'c454b4e4c3d881b2a78361c5868212f734c458291a3cb28be8ba4a63030eb004';

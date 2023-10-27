// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunGroupPanelQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
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
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

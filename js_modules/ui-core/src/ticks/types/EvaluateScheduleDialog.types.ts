// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type GetScheduleQueryVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
  startTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
  ticksAfter?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  ticksBefore?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type GetScheduleQuery = {
  __typename: 'Query';
  scheduleOrError:
    | {__typename: 'PythonError'; message: string; stack: Array<string>}
    | {__typename: 'Schedule'; id: string; name: string; potentialTickTimestamps: Array<number>}
    | {__typename: 'ScheduleNotFoundError'};
};

export type ScheduleDryRunMutationVariables = Types.Exact<{
  selectorData: Types.ScheduleSelector;
  timestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
}>;

export type ScheduleDryRunMutation = {
  __typename: 'Mutation';
  scheduleDryRun:
    | {
        __typename: 'DryRunInstigationTick';
        timestamp: number | null;
        evaluationResult: {
          __typename: 'TickEvaluation';
          skipReason: string | null;
          runRequests: Array<{
            __typename: 'RunRequest';
            runConfigYaml: string;
            runKey: string | null;
            jobName: string | null;
            tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
            assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
            assetChecks: Array<{
              __typename: 'AssetCheckhandle';
              name: string;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }> | null;
          }> | null;
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
        } | null;
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
      }
    | {__typename: 'ScheduleNotFoundError'; scheduleName: string};
};

export const ScheduleDryRunMutationVersion = '130e70022d3025cc2ba6c88a553282f2c92335ac0a380cfda0307c663280f1f8';

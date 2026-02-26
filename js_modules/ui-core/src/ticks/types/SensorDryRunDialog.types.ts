// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SensorDryRunMutationVariables = Types.Exact<{
  selectorData: Types.SensorSelector;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type SensorDryRunMutation = {
  __typename: 'Mutation';
  sensorDryRun:
    | {
        __typename: 'DryRunInstigationTick';
        timestamp: number | null;
        evaluationResult: {
          __typename: 'TickEvaluation';
          cursor: string | null;
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
          dynamicPartitionsRequests: Array<{
            __typename: 'DynamicPartitionRequest';
            partitionKeys: Array<string> | null;
            partitionsDefName: string;
            type: Types.DynamicPartitionsRequestType;
          }> | null;
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
    | {__typename: 'SensorNotFoundError'};
};

export type DynamicPartitionRequestFragment = {
  __typename: 'DynamicPartitionRequest';
  partitionKeys: Array<string> | null;
  partitionsDefName: string;
  type: Types.DynamicPartitionsRequestType;
};

export const SensorDryRunMutationVersion = '41baf2a82bbd8cd13f8c34ca3dfdd506fef6d5607c366328e20a50ebac662d0a';

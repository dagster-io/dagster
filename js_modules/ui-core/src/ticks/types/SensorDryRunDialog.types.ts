/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DynamicPartitionsRequestType = 'ADD_PARTITIONS' | 'DELETE_PARTITIONS';

export type SensorSelector = {
  repositoryLocationName: string;
  repositoryName: string;
  sensorName: string;
};

export type SensorDryRunMutationVariables = Exact<{
  selectorData: Types.SensorSelector;
  cursor?: string | null | undefined;
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
          assetEvents: Array<string> | null;
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
    | {__typename: 'SensorNotFoundError'}
    | {__typename: 'UnauthorizedError'};
};

export type DynamicPartitionRequestFragment = {
  __typename: 'DynamicPartitionRequest';
  partitionKeys: Array<string> | null;
  partitionsDefName: string;
  type: Types.DynamicPartitionsRequestType;
};

export type ReportSensorTickAssetEventsMutationVariables = Exact<{
  assetEvents: Array<string> | string;
}>;

export type ReportSensorTickAssetEventsMutation = {
  __typename: 'Mutation';
  reportSensorTickAssetEvents:
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
        __typename: 'ReportSensorTickAssetEventsPartialFailure';
        remainingAssetEvents: Array<string>;
        reportedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        };
      }
    | {
        __typename: 'ReportSensorTickAssetEventsSuccess';
        assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      }
    | {__typename: 'UnauthorizedError'};
};

export const SensorDryRunMutationVersion = 'f7fb6e82a40377ce40403c137eff1f7efa15f950c9cf118c7f5d4596f968b0ef';

export const ReportSensorTickAssetEventsMutationVersion = '6fcbb89f4000a892063600cf77990e21a340b27a25628c2c5cc1d18ba6840d73';

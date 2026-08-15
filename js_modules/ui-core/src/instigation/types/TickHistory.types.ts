/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DynamicPartitionsRequestType = 'ADD_PARTITIONS' | 'DELETE_PARTITIONS';

export type InstigationSelector = {
  name: string;
  repositoryLocationName: string;
  repositoryName: string;
};

export type InstigationTickStatus = 'FAILURE' | 'SKIPPED' | 'STARTED' | 'SUCCESS';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

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

export type TickHistoryQueryVariables = Exact<{
  instigationSelector: Types.InstigationSelector;
  dayRange?: number | null | undefined;
  limit?: number | null | undefined;
  cursor?: string | null | undefined;
  statuses?: Array<Types.InstigationTickStatus> | Types.InstigationTickStatus | null | undefined;
  beforeTimestamp?: number | null | undefined;
  afterTimestamp?: number | null | undefined;
}>;

export type TickHistoryQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        instigationType: Types.InstigationType;
        ticks: Array<{
          __typename: 'InstigationTick';
          id: string;
          tickId: string;
          status: Types.InstigationTickStatus;
          timestamp: number;
          endTimestamp: number | null;
          cursor: string | null;
          instigationType: Types.InstigationType;
          skipReason: string | null;
          requestedAssetMaterializationCount: number;
          requestedJobRunCount: number;
          runIds: Array<string>;
          originRunIds: Array<string>;
          logKey: Array<string> | null;
          runKeys: Array<string>;
          runs: Array<{__typename: 'Run'; id: string; status: Types.RunStatus}>;
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
          dynamicPartitionsRequestResults: Array<{
            __typename: 'DynamicPartitionsRequestResult';
            partitionsDefName: string;
            partitionKeys: Array<string> | null;
            skippedPartitionKeys: Array<string>;
            type: Types.DynamicPartitionsRequestType;
          }>;
        }>;
      }
    | {__typename: 'InstigationStateNotFoundError'}
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

export const TickHistoryQueryVersion = 'ed93ec15eb533d05b50d44616bc0f4bba3255d6bbd2c36539c6fa783dc7f0298';

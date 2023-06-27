// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TickHistoryQueryVariables = Types.Exact<{
  instigationSelector: Types.InstigationSelector;
  dayRange?: Types.InputMaybe<Types.Scalars['Int']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']>;
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
  statuses?: Types.InputMaybe<Array<Types.InstigationTickStatus> | Types.InstigationTickStatus>;
}>;

export type TickHistoryQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        instigationType: Types.InstigationType;
        nextTick: {__typename: 'DryRunInstigationTick'; timestamp: number | null} | null;
        ticks: Array<{
          __typename: 'InstigationTick';
          id: string;
          status: Types.InstigationTickStatus;
          timestamp: number;
          cursor: string | null;
          skipReason: string | null;
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

export type NextTickForHistoryFragment = {
  __typename: 'DryRunInstigationTick';
  timestamp: number | null;
};

export type HistoryTickFragment = {
  __typename: 'InstigationTick';
  id: string;
  status: Types.InstigationTickStatus;
  timestamp: number;
  cursor: string | null;
  skipReason: string | null;
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
};

export type DynamicPartitionsRequestResultFragment = {
  __typename: 'DynamicPartitionsRequestResult';
  partitionsDefName: string;
  partitionKeys: Array<string> | null;
  skippedPartitionKeys: Array<string>;
  type: Types.DynamicPartitionsRequestType;
};

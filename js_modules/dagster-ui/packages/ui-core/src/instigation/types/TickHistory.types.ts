// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TickHistoryQueryVariables = Types.Exact<{
  instigationSelector: Types.InstigationSelector;
  dayRange?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  statuses?: Types.InputMaybe<Array<Types.InstigationTickStatus> | Types.InstigationTickStatus>;
  beforeTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
  afterTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
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

export const TickHistoryQueryVersion = '4dff0791129120937abefb56bf6b21102cd3b67f81f7285763f01d6467f850e8';

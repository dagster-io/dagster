// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckPartitionHealthQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  checkName: Types.Scalars['String']['input'];
}>;

export type AssetCheckPartitionHealthQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        assetChecksOrError:
          | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
          | {__typename: 'AssetCheckNeedsMigrationError'}
          | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
          | {
              __typename: 'AssetChecks';
              checks: Array<{
                __typename: 'AssetCheck';
                name: string;
                partitionKeysByDimension: Array<{
                  __typename: 'DimensionPartitionKeys';
                  name: string;
                  partitionKeys: Array<string>;
                }>;
              }>;
            };
      }
    | {__typename: 'AssetNotFoundError'};
  assetCheckExecutions: Array<{
    __typename: 'AssetCheckExecution';
    id: string;
    status: Types.AssetCheckExecutionResolvedStatus;
    evaluation: {
      __typename: 'AssetCheckEvaluation';
      success: boolean;
      partition: string | null;
    } | null;
  }>;
};

export const AssetCheckPartitionHealthQueryVersion = 'd900b12f7b169e196c455d8e9bb1e7d7b1434f47e8a335be228d072ad4a7b891';

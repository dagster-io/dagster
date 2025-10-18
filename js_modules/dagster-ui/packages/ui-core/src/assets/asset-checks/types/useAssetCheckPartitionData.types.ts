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
        assetCheckOrError:
          | {
              __typename: 'AssetCheck';
              name: string;
              partitionKeysByDimension: Array<{
                __typename: 'DimensionPartitionKeys';
                name: string;
                partitionKeys: Array<string>;
              }>;
              partitionStatuses: {
                __typename: 'AssetCheckPartitionStatuses';
                missing: Array<string>;
                succeeded: Array<string>;
                failed: Array<string>;
                inProgress: Array<string>;
                skipped: Array<string>;
                executionFailed: Array<string>;
              } | null;
            }
          | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
          | {__typename: 'AssetCheckNeedsMigrationError'}
          | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
          | {__typename: 'AssetCheckNotFoundError'};
      }
    | {__typename: 'AssetNotFoundError'};
};

export const AssetCheckPartitionHealthQueryVersion = '85d84ebb07a4f45fa3c774e3c2bbaa51eeeb4215cd7a95ea374bd2ce9e10656a';

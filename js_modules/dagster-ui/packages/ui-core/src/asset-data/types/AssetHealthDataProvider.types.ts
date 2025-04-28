// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetHealthQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetHealthQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    assetHealth: {
      __typename: 'AssetHealth';
      assetHealth: Types.AssetHealthStatus;
      materializationStatus: Types.AssetHealthStatus;
      assetChecksStatus: Types.AssetHealthStatus;
      freshnessStatus: Types.AssetHealthStatus;
      materializationStatusMetadata:
        | {__typename: 'AssetHealthMaterializationDegradedNotPartitionedMeta'; failedRunId: string}
        | {
            __typename: 'AssetHealthMaterializationDegradedPartitionedMeta';
            numMissingPartitions: number;
            numFailedPartitions: number;
            totalNumPartitions: number;
          }
        | {
            __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
            numMissingPartitions: number;
            totalNumPartitions: number;
          }
        | null;
      assetChecksStatusMetadata:
        | {
            __typename: 'AssetHealthCheckDegradedMeta';
            numFailedChecks: number;
            numWarningChecks: number;
            totalNumChecks: number;
          }
        | {
            __typename: 'AssetHealthCheckUnknownMeta';
            numNotExecutedChecks: number;
            totalNumChecks: number;
          }
        | {
            __typename: 'AssetHealthCheckWarningMeta';
            numWarningChecks: number;
            totalNumChecks: number;
          }
        | null;
      freshnessStatusMetadata: {
        __typename: 'AssetHealthFreshnessMeta';
        lastMaterializedTimestamp: number | null;
      } | null;
    } | null;
  }>;
};

export type AssetHealthFragment = {
  __typename: 'AssetNode';
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  assetHealth: {
    __typename: 'AssetHealth';
    assetHealth: Types.AssetHealthStatus;
    materializationStatus: Types.AssetHealthStatus;
    assetChecksStatus: Types.AssetHealthStatus;
    freshnessStatus: Types.AssetHealthStatus;
    materializationStatusMetadata:
      | {__typename: 'AssetHealthMaterializationDegradedNotPartitionedMeta'; failedRunId: string}
      | {
          __typename: 'AssetHealthMaterializationDegradedPartitionedMeta';
          numMissingPartitions: number;
          numFailedPartitions: number;
          totalNumPartitions: number;
        }
      | {
          __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
          numMissingPartitions: number;
          totalNumPartitions: number;
        }
      | null;
    assetChecksStatusMetadata:
      | {
          __typename: 'AssetHealthCheckDegradedMeta';
          numFailedChecks: number;
          numWarningChecks: number;
          totalNumChecks: number;
        }
      | {
          __typename: 'AssetHealthCheckUnknownMeta';
          numNotExecutedChecks: number;
          totalNumChecks: number;
        }
      | {
          __typename: 'AssetHealthCheckWarningMeta';
          numWarningChecks: number;
          totalNumChecks: number;
        }
      | null;
    freshnessStatusMetadata: {
      __typename: 'AssetHealthFreshnessMeta';
      lastMaterializedTimestamp: number | null;
    } | null;
  } | null;
};

export type AssetHealthMaterializationDegradedPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationDegradedPartitionedMeta';
  numMissingPartitions: number;
  numFailedPartitions: number;
  totalNumPartitions: number;
};

export type AssetHealthMaterializationHealthyPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
  numMissingPartitions: number;
  totalNumPartitions: number;
};

export type AssetHealthMaterializationDegradedNotPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationDegradedNotPartitionedMeta';
  failedRunId: string;
};

export type AssetHealthCheckDegradedMetaFragment = {
  __typename: 'AssetHealthCheckDegradedMeta';
  numFailedChecks: number;
  numWarningChecks: number;
  totalNumChecks: number;
};

export type AssetHealthCheckWarningMetaFragment = {
  __typename: 'AssetHealthCheckWarningMeta';
  numWarningChecks: number;
  totalNumChecks: number;
};

export type AssetHealthCheckUnknownMetaFragment = {
  __typename: 'AssetHealthCheckUnknownMeta';
  numNotExecutedChecks: number;
  totalNumChecks: number;
};

export type AssetHealthFreshnessMetaFragment = {
  __typename: 'AssetHealthFreshnessMeta';
  lastMaterializedTimestamp: number | null;
};

export const AssetHealthQueryVersion = 'a72664fb39652fac6bd55ac1ea4cd5b52f429d89d7d0c05ee41d26be19f7721d';

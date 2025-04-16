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
            totalNumPartitions: number;
          }
        | {
            __typename: 'AssetHealthMaterializationWarningPartitionedMeta';
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
          totalNumPartitions: number;
        }
      | {
          __typename: 'AssetHealthMaterializationWarningPartitionedMeta';
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
  totalNumPartitions: number;
};

export type AssetHealthMaterializationWarningPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationWarningPartitionedMeta';
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

export const AssetHealthQueryVersion = '79029e5084496e14147e615fa7cf65f4f61d71add7ac519720e1911fbe0bdbc2';

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

export const AssetHealthQueryVersion = '564cb745963722748aeaac66dc433a44e8b6091ef60812a0bb7ec44c3fae5b1c';

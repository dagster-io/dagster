// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetHealthQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetHealthQuery = {
  __typename: 'Query';
  assetsOrError:
    | {
        __typename: 'AssetConnection';
        nodes: Array<{
          __typename: 'Asset';
          id: string;
          latestMaterializationTimestamp: number | null;
          key: {__typename: 'AssetKey'; path: Array<string>};
          assetHealth: {
            __typename: 'AssetHealth';
            assetHealth: Types.AssetHealthStatus;
            materializationStatus: Types.AssetHealthStatus;
            assetChecksStatus: Types.AssetHealthStatus;
            freshnessStatus: Types.AssetHealthStatus;
            materializationStatusMetadata:
              | {
                  __typename: 'AssetHealthMaterializationDegradedNotPartitionedMeta';
                  failedRunId: string;
                }
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
      };
};

export type AssetHealthFragment = {
  __typename: 'Asset';
  latestMaterializationTimestamp: number | null;
  key: {__typename: 'AssetKey'; path: Array<string>};
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

export const AssetHealthQueryVersion = '4b2085823a75ee438b8786c2e65a0611bba1abe02d04b327a508bde77f445f92';

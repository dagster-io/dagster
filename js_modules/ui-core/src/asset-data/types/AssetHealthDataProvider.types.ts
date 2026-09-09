/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetHealthStatus = 'DEGRADED' | 'HEALTHY' | 'NOT_APPLICABLE' | 'UNKNOWN' | 'WARNING';

export type AssetKeyInput = {
  path: Array<string>;
};

export type AssetHealthQueryVariables = Exact<{
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
          latestFailedToMaterializeTimestamp: number | null;
          freshnessStatusChangedTimestamp: number | null;
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
                  failedRunId: string | null;
                }
              | {
                  __typename: 'AssetHealthMaterializationDegradedPartitionedMeta';
                  numMissingPartitions: number;
                  numFailedPartitions: number;
                  totalNumPartitions: number;
                  latestFailedRunId: string | null;
                }
              | {
                  __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
                  numMissingPartitions: number;
                  totalNumPartitions: number;
                  latestRunId: string | null;
                }
              | {
                  __typename: 'AssetHealthMaterializationWarningNotPartitionedMeta';
                  failedRunId: string | null;
                }
              | {
                  __typename: 'AssetHealthMaterializationWarningPartitionedMeta';
                  numUpForRetryPartitions: number;
                  numMissingPartitions: number;
                  totalNumPartitions: number;
                  latestRunId: string | null;
                  latestFailedRunId: string | null;
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
  id: string;
  latestMaterializationTimestamp: number | null;
  latestFailedToMaterializeTimestamp: number | null;
  freshnessStatusChangedTimestamp: number | null;
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
          failedRunId: string | null;
        }
      | {
          __typename: 'AssetHealthMaterializationDegradedPartitionedMeta';
          numMissingPartitions: number;
          numFailedPartitions: number;
          totalNumPartitions: number;
          latestFailedRunId: string | null;
        }
      | {
          __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
          numMissingPartitions: number;
          totalNumPartitions: number;
          latestRunId: string | null;
        }
      | {
          __typename: 'AssetHealthMaterializationWarningNotPartitionedMeta';
          failedRunId: string | null;
        }
      | {
          __typename: 'AssetHealthMaterializationWarningPartitionedMeta';
          numUpForRetryPartitions: number;
          numMissingPartitions: number;
          totalNumPartitions: number;
          latestRunId: string | null;
          latestFailedRunId: string | null;
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
  latestFailedRunId: string | null;
};

export type AssetHealthMaterializationHealthyPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
  numMissingPartitions: number;
  totalNumPartitions: number;
  latestRunId: string | null;
};

export type AssetHealthMaterializationDegradedNotPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationDegradedNotPartitionedMeta';
  failedRunId: string | null;
};

export type AssetHealthMaterializationWarningPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationWarningPartitionedMeta';
  numUpForRetryPartitions: number;
  numMissingPartitions: number;
  totalNumPartitions: number;
  latestRunId: string | null;
  latestFailedRunId: string | null;
};

export type AssetHealthMaterializationWarningNotPartitionedMetaFragment = {
  __typename: 'AssetHealthMaterializationWarningNotPartitionedMeta';
  failedRunId: string | null;
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

export const AssetHealthQueryVersion = '4fa08d7ab1b2237a6f7b4b18ea5b24bf6d7c19398e7cd68c618175de3c12f7c0';

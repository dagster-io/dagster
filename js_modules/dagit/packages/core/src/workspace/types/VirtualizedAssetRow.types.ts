// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleAssetQueryVariables = Types.Exact<{
  input: Types.AssetKeyInput;
}>;

export type SingleAssetQuery = {
  __typename: 'DagitQuery';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        assetMaterializations: Array<{
          __typename: 'MaterializationEvent';
          runId: string;
          timestamp: string;
        }>;
        definition: {
          __typename: 'AssetNode';
          id: string;
          computeKind: string | null;
          opNames: Array<string>;
          currentLogicalVersion: string | null;
          projectedLogicalVersion: string | null;
          groupName: string | null;
          isSource: boolean;
          description: string | null;
          repository: {
            __typename: 'Repository';
            id: string;
            name: string;
            location: {__typename: 'RepositoryLocation'; id: string; name: string};
          };
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          assetMaterializations: Array<{
            __typename: 'MaterializationEvent';
            timestamp: string;
            runId: string;
          }>;
          freshnessPolicy: {
            __typename: 'FreshnessPolicy';
            maximumLagMinutes: number;
            cronSchedule: string | null;
          } | null;
          freshnessInfo: {
            __typename: 'AssetFreshnessInfo';
            currentMinutesLate: number | null;
          } | null;
          assetObservations: Array<{
            __typename: 'ObservationEvent';
            timestamp: string;
            runId: string;
          }>;
          partitionStats: {
            __typename: 'PartitionStats';
            numMaterialized: number;
            numPartitions: number;
          } | null;
          partitionDefinition: {__typename: 'PartitionDefinition'; description: string} | null;
        } | null;
        key: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'AssetNotFoundError'};
  assetsLatestInfo: Array<{
    __typename: 'AssetLatestInfo';
    unstartedRunIds: Array<string>;
    inProgressRunIds: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    latestRun: {
      __typename: 'Run';
      id: string;
      status: Types.RunStatus;
      endTime: number | null;
    } | null;
  }>;
};

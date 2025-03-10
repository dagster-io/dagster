import {
  AssetCheckLiveFragment,
  AssetLatestInfoFragment,
  AssetLatestInfoRunFragment,
  AssetNodeLiveFragment,
  AssetNodeLiveFreshnessInfoFragment,
  AssetNodeLiveMaterializationFragment,
  AssetNodeLiveObservationFragment,
} from '../asset-data/types/AssetBaseDataQueries.types';
import {AssetStaleDataFragment} from '../asset-data/types/AssetStaleStatusDataProvider.types';
import {RunStatus} from '../graphql/types';

export type AssetLiveNodeOSS = AssetNodeLiveFragment & {
  freshnessInfo: AssetNodeLiveFreshnessInfoFragment | null | undefined;
};
export type AssetLatestInfoOSS = AssetLatestInfoFragment;

export type OSSLiveDataForNode = {
  stepKey: string;
  unstartedRunIds: string[]; // run in progress and step not started
  inProgressRunIds: string[]; // run in progress and step in progress
  runWhichFailedToMaterialize: AssetLatestInfoRunFragment | null;
  lastMaterialization: AssetNodeLiveMaterializationFragment | null;
  lastMaterializationRunStatus: RunStatus | null; // only available if runWhichFailedToMaterialize is null
  freshnessInfo: AssetNodeLiveFreshnessInfoFragment | null | undefined;
  lastObservation: AssetNodeLiveObservationFragment | null;
  assetChecks: AssetCheckLiveFragment[];
  partitionStats: {
    numMaterialized: number;
    numMaterializing: number;
    numPartitions: number;
    numFailed: number;
  } | null;
  opNames: string[];
};

export interface OSSLiveDataForNodeWithStaleData extends OSSLiveDataForNode {
  staleStatus: AssetStaleDataFragment['staleStatus'];
  staleCauses: AssetStaleDataFragment['staleCauses'];
}

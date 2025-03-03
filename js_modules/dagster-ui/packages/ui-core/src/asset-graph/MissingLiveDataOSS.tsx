import {OSSLiveDataForNodeWithStaleData} from './OSSLiveDataForNode';

export const MISSING_LIVE_DATA_OSS: OSSLiveDataForNodeWithStaleData = {
  unstartedRunIds: [],
  inProgressRunIds: [],
  runWhichFailedToMaterialize: null,
  freshnessInfo: null,
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  partitionStats: null,
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  opNames: [],
  stepKey: '',
};

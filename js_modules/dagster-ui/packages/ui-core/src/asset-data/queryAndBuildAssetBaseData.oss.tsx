import {LiveDataForNode} from 'shared/asset-graph/LiveDataForNode.oss';

import {queryAndBuildAssetBaseOSSData} from './queryAndBuildAssetBaseOSSData';
import {ApolloClient} from '../apollo-client';

export const queryAndBuildAssetBaseData = async (
  keys: string[],
  client: ApolloClient<any>,
): Promise<Record<string, LiveDataForNode>> => {
  return queryAndBuildAssetBaseOSSData(keys, client);
};

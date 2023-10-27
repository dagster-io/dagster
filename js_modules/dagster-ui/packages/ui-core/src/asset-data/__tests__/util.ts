import {
  AssetKeyInput,
  buildAssetNode,
  buildAssetKey,
  buildAssetLatestInfo,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {ASSETS_GRAPH_LIVE_QUERY} from '../AssetLiveDataProvider';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from '../types/AssetLiveDataProvider.types';

export function buildMockedAssetGraphLiveQuery(assetKeys: AssetKeyInput[]) {
  return buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {
      // strip __typename
      assetKeys: assetKeys.map((assetKey) => ({path: assetKey.path})),
    },
    data: {
      assetNodes: assetKeys.map((assetKey) =>
        buildAssetNode({assetKey: buildAssetKey(assetKey), id: JSON.stringify(assetKey)}),
      ),
      assetsLatestInfo: assetKeys.map((assetKey) =>
        buildAssetLatestInfo({assetKey: buildAssetKey(assetKey), id: JSON.stringify(assetKey)}),
      ),
    },
  });
}

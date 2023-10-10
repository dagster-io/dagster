import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from '../../asset-graph/types/useLiveDataForAssetKeys.types';
import {ASSETS_GRAPH_LIVE_QUERY} from '../../asset-graph/useLiveDataForAssetKeys';
import {
  AssetKeyInput,
  buildAssetNode,
  buildAssetKey,
  buildAssetLatestInfo,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';

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

import {GraphQLError} from 'graphql/error';

import {
  AssetKeyInput,
  buildAssetKey,
  buildAssetLatestInfo,
  buildAssetNode,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {ASSETS_GRAPH_LIVE_QUERY} from '../AssetLiveDataThread';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from '../types/AssetLiveDataThread.types';

export function buildMockedAssetGraphLiveQuery(
  assetKeys: AssetKeyInput[],
  data:
    | Parameters<
        typeof buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>
      >[0]['data']
    | undefined = undefined,
  errors: readonly GraphQLError[] | undefined = undefined,
) {
  return buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {
      // strip __typename
      assetKeys: assetKeys.map((assetKey) => ({path: assetKey.path})),
    },
    data:
      data === undefined && errors === undefined
        ? {
            assetNodes: assetKeys.map((assetKey) =>
              buildAssetNode({assetKey: buildAssetKey(assetKey), id: JSON.stringify(assetKey)}),
            ),
            assetsLatestInfo: assetKeys.map((assetKey) =>
              buildAssetLatestInfo({
                assetKey: buildAssetKey(assetKey),
                id: JSON.stringify(assetKey),
              }),
            ),
          }
        : data,
    errors,
  });
}

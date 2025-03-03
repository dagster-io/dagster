import {GraphQLError} from 'graphql/error';

import {
  AssetKeyInput,
  buildAssetKey,
  buildAssetLatestInfo,
  buildAssetNode,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {ASSETS_FRESHNESS_INFO_QUERY, ASSETS_GRAPH_LIVE_QUERY} from '../AssetBaseDataQueries';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetsFreshnessInfoQuery,
  AssetsFreshnessInfoQueryVariables,
} from '../types/AssetBaseDataQueries.types';

export function buildMockedAssetGraphLiveQuery(
  assetKeys: AssetKeyInput[],
  data:
    | Parameters<
        typeof buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>
      >[0]['data']
    | undefined = undefined,
  errors: readonly GraphQLError[] | undefined = undefined,
) {
  const opts = {
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
  };
  return [
    buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
      query: ASSETS_GRAPH_LIVE_QUERY,
      ...opts,
    }),
    buildQueryMock<AssetsFreshnessInfoQuery, AssetsFreshnessInfoQueryVariables>({
      query: ASSETS_FRESHNESS_INFO_QUERY,
      ...opts,
      data:
        data === undefined && errors === undefined
          ? {
              assetNodes: assetKeys.map((assetKey) =>
                buildAssetNode({assetKey: buildAssetKey(assetKey), id: JSON.stringify(assetKey)}),
              ),
            }
          : undefined,
    }),
  ] as const;
}

import {ApolloClient} from '../apollo-client';
import {ASSETS_FRESHNESS_INFO_QUERY, ASSETS_GRAPH_LIVE_QUERY} from './AssetBaseDataQueries';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetLatestInfoFragment,
  AssetNodeLiveFragment,
  AssetNodeLiveFreshnessInfoFragment,
  AssetsFreshnessInfoQuery,
  AssetsFreshnessInfoQueryVariables,
} from './types/AssetBaseDataQueries.types';
import {OSSLiveDataForNode} from '../asset-graph/OSSLiveDataForNode';
import {
  shouldDisplayRunFailure,
  stepKeyForAsset,
  tokenForAssetKey,
  tokenToAssetKey,
} from '../asset-graph/Utils';

type AssetLiveNode = AssetNodeLiveFragment & {
  freshnessInfo: AssetNodeLiveFreshnessInfoFragment | null | undefined;
};
type AssetLatestInfo = AssetLatestInfoFragment;

export const queryAndBuildAssetBaseOSSData = async (
  keys: string[],
  client: ApolloClient<any>,
): Promise<Record<string, OSSLiveDataForNode>> => {
  const assetKeys = keys.map(tokenToAssetKey);
  const [graphResponse, freshnessResponse] = await Promise.all([
    client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
      query: ASSETS_GRAPH_LIVE_QUERY,
      fetchPolicy: 'no-cache',
      variables: {
        assetKeys,
      },
    }),
    client.query<AssetsFreshnessInfoQuery, AssetsFreshnessInfoQueryVariables>({
      query: ASSETS_FRESHNESS_INFO_QUERY,
      fetchPolicy: 'no-cache',
      variables: {
        assetKeys,
      },
    }),
  ]);

  const {data} = graphResponse;
  const {data: freshnessData} = freshnessResponse;

  const nodesByKey = Object.fromEntries(
    data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
  );

  const freshnessInfoByKey = Object.fromEntries(
    freshnessData.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
  );

  return Object.fromEntries(
    data.assetsLatestInfo
      .map((assetLatestInfo) => {
        const id = tokenForAssetKey(assetLatestInfo.assetKey);
        const node = nodesByKey[id];
        const freshnessInfo = freshnessInfoByKey[id];
        return node
          ? [
              id,
              buildLiveDataForNode(
                {
                  ...node,
                  ...(freshnessInfo ?? {
                    freshnessInfo: null,
                  }),
                },
                assetLatestInfo,
              ),
            ]
          : null;
      })
      .filter((entry): entry is [string, OSSLiveDataForNode] => !!entry),
  );
};

const buildLiveDataForNode = (
  assetNode: AssetLiveNode,
  assetLatestInfo?: AssetLatestInfo,
): OSSLiveDataForNode => {
  const lastMaterialization = assetNode.assetMaterializations[0] || null;
  const lastObservation = assetNode.assetObservations[0] || null;
  const latestRun = assetLatestInfo?.latestRun ? assetLatestInfo.latestRun : null;

  return {
    lastMaterialization,
    lastMaterializationRunStatus:
      latestRun && lastMaterialization?.runId === latestRun.id ? latestRun.status : null,
    lastObservation,
    assetChecks:
      assetNode.assetChecksOrError.__typename === 'AssetChecks'
        ? assetNode.assetChecksOrError.checks
        : [],
    stepKey: stepKeyForAsset(assetNode),
    freshnessInfo: assetNode.freshnessInfo,
    inProgressRunIds: assetLatestInfo?.inProgressRunIds || [],
    unstartedRunIds: assetLatestInfo?.unstartedRunIds || [],
    partitionStats: assetNode.partitionStats || null,
    runWhichFailedToMaterialize:
      latestRun && shouldDisplayRunFailure(latestRun, lastMaterialization) ? latestRun : null,
    opNames: assetNode.opNames,
  };
};

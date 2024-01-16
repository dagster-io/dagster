import {ApolloClient, gql} from '@apollo/client';

import {LiveDataForNode, tokenForAssetKey, buildLiveDataForNode} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';

import type {AssetLiveDataThreadManager} from './AssetLiveDataThreadManager';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetNodeLiveFragment,
} from './types/AssetLiveDataThread.types';
import {BATCHING_INTERVAL} from './util';

export type AssetLiveDataThreadID = 'default' | 'sidebar' | 'asset-graph' | 'group-node';

export class AssetLiveDataThread {
  private isFetching: boolean = false;
  private listenersCount: {[key: string]: number};
  private client: ApolloClient<any>;
  private isLooping: boolean = false;
  private interval?: ReturnType<typeof setTimeout>;
  private manager: AssetLiveDataThreadManager;
  public pollRate: number = 30000;

  protected static _threads: {[key: string]: AssetLiveDataThread} = {};

  constructor(client: ApolloClient<any>, manager: AssetLiveDataThreadManager) {
    this.client = client;
    this.listenersCount = {};
    this.manager = manager;
  }

  public setPollRate(pollRate: number) {
    this.pollRate = pollRate;
  }

  public subscribe(key: string) {
    this.listenersCount[key] = this.listenersCount[key] || 0;
    this.listenersCount[key] += 1;
    this.startFetchLoop();
  }

  public unsubscribe(key: string) {
    this.listenersCount[key] -= 1;
    if (this.listenersCount[key] === 0) {
      delete this.listenersCount[key];
    }
    if (this.getObservedKeys().length === 0) {
      this.stopFetchLoop();
    }
  }

  public getObservedKeys() {
    return Object.keys(this.listenersCount);
  }

  public startFetchLoop() {
    if (this.isLooping) {
      return;
    }
    this.isLooping = true;
    const fetch = () => {
      const nextAssets = this.manager.determineAssetsToFetch(this.getObservedKeys());
      if (nextAssets.length) {
        this._batchedQueryAssets(nextAssets);
      }
    };
    setTimeout(fetch, BATCHING_INTERVAL);
    this.interval = setInterval(fetch, 5000);
  }

  public stopFetchLoop() {
    if (!this.isLooping) {
      return;
    }
    this.isLooping = false;
    clearInterval(this.interval);
    this.interval = undefined;
  }

  private async queryAssetKeys(assetKeys: AssetKeyInput[]) {
    const {data} = await this.client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
      query: ASSETS_GRAPH_LIVE_QUERY,
      fetchPolicy: 'network-only',
      variables: {
        assetKeys,
      },
    });
    const nodesByKey: Record<string, AssetNodeLiveFragment> = {};
    const liveDataByKey: Record<string, LiveDataForNode> = {};
    data.assetNodes.forEach((assetNode) => {
      const id = tokenForAssetKey(assetNode.assetKey);
      nodesByKey[id] = assetNode;
    });
    data.assetsLatestInfo.forEach((assetLatestInfo) => {
      const id = tokenForAssetKey(assetLatestInfo.assetKey);
      liveDataByKey[id] = buildLiveDataForNode(nodesByKey[id]!, assetLatestInfo);
    });

    this.manager._updateCache(liveDataByKey);
    return liveDataByKey;
  }

  private async _batchedQueryAssets(assetKeys: AssetKeyInput[]) {
    if (!assetKeys.length || this.isFetching) {
      return;
    }
    this.isFetching = true;
    this.manager._markAssetsRequested(assetKeys);

    const doNextFetch = () => {
      this.isFetching = false;
      const nextAssets = this.manager.determineAssetsToFetch(this.getObservedKeys());
      if (nextAssets.length) {
        this._batchedQueryAssets(nextAssets);
      }
    };
    try {
      const data = await this.queryAssetKeys(assetKeys);
      this.manager._updateFetchedAssets(assetKeys, data);
      doNextFetch();
    } catch (e) {
      console.error(e);

      if ((e as any)?.message?.includes('500')) {
        // Mark these assets as fetched so that we don't retry them until after the poll interval rather than retrying them immediately.
        // This is preferable because if the assets failed to fetch it's likely due to a timeout due to the query being too expensive and retrying it
        // will not make it more likely to succeed and it would add more load to the database.
        this.manager._updateFetchedAssets(assetKeys, {});
      } else {
        // If it's not a timeout from the backend then lets keep retrying instead of moving on.
        this.manager._unmarkAssetsRequested(assetKeys);
      }

      setTimeout(
        () => {
          doNextFetch();
        },
        // If the poll rate is faster than 5 seconds lets use that instead
        Math.min(this.pollRate, 5000),
      );
    }
  }
}

export const ASSET_LATEST_INFO_FRAGMENT = gql`
  fragment AssetLatestInfoFragment on AssetLatestInfo {
    id
    assetKey {
      path
    }
    unstartedRunIds
    inProgressRunIds
    latestRun {
      id
      ...AssetLatestInfoRun
    }
  }

  fragment AssetLatestInfoRun on Run {
    status
    endTime
    id
  }
`;

export const ASSET_NODE_LIVE_FRAGMENT = gql`
  fragment AssetNodeLiveFragment on AssetNode {
    id
    opNames
    repository {
      id
    }
    assetKey {
      path
    }
    assetMaterializations(limit: 1) {
      ...AssetNodeLiveMaterialization
    }
    assetObservations(limit: 1) {
      ...AssetNodeLiveObservation
    }
    assetChecksOrError {
      ... on AssetChecks {
        checks {
          ...AssetCheckLiveFragment
        }
      }
    }
    freshnessInfo {
      ...AssetNodeLiveFreshnessInfo
    }
    staleStatus
    staleCauses {
      key {
        path
      }
      reason
      category
      dependency {
        path
      }
    }
    partitionStats {
      numMaterialized
      numMaterializing
      numPartitions
      numFailed
    }
  }

  fragment AssetNodeLiveFreshnessInfo on AssetFreshnessInfo {
    currentMinutesLate
  }

  fragment AssetNodeLiveMaterialization on MaterializationEvent {
    timestamp
    runId
  }

  fragment AssetNodeLiveObservation on ObservationEvent {
    timestamp
    runId
  }

  fragment AssetCheckLiveFragment on AssetCheck {
    name
    canExecuteIndividually
    executionForLatestMaterialization {
      id
      runId
      status
      timestamp
      stepKey
      evaluation {
        severity
      }
    }
  }
`;

export const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
    assetsLatestInfo(assetKeys: $assetKeys) {
      ...AssetLatestInfoFragment
    }
  }

  ${ASSET_NODE_LIVE_FRAGMENT}
  ${ASSET_LATEST_INFO_FRAGMENT}
`;

import reject from 'lodash/reject';
import {useEffect, useLayoutEffect, useMemo, useState} from 'react';
import {useAssetGraphSupplementaryData} from 'shared/asset-graph/useAssetGraphSupplementaryData.oss';

import {computeGraphData} from './ComputeGraphData';
import {GraphData, buildGraphData, tokenForAssetKey} from './Utils';
import {AssetGraphQueryItem, AssetNode} from './types';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {useShowAssetsWithoutDefinitions} from '../app/UserSettingsDialog/useShowAssetsWithoutDefinitions';
import {useShowStubAssets} from '../app/UserSettingsDialog/useShowStubAssets';
import {AssetKey} from '../assets/types';
import {useAllAssetsNodes} from '../assets/useAllAssets';
import {AssetGroupSelector, PipelineSelector} from '../graphql/types';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {WorkspaceAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

export interface AssetGraphFetchScope {
  hideEdgesToNodesOutsideQuery?: boolean;
  hideNodesMatching?: (node: WorkspaceAssetFragment) => boolean;
  pipelineSelector?: Pick<
    PipelineSelector,
    'pipelineName' | 'repositoryName' | 'repositoryLocationName'
  >;
  groupSelector?: Pick<
    AssetGroupSelector,
    'groupName' | 'repositoryName' | 'repositoryLocationName'
  >;
  kinds?: string[];

  externalAssets?: {id: string; key: {path: Array<string>}}[];

  // This is used to indicate we shouldn't start handling any input.
  // This is used by pages where `hideNodesMatching` is only available asynchronously.
  loading?: boolean;
  skip?: boolean;
}

export function useFullAssetGraphData(
  options: Omit<AssetGraphFetchScope, 'groupSelector' | 'pipelineSelector'>,
) {
  const {assets, loading} = useAllAssetsNodes();

  const {showStubAssets} = useShowStubAssets();
  const {showAssetsWithoutDefinitions} = useShowAssetsWithoutDefinitions();

  const allNodes = useMemo(
    () =>
      getAllAssets(
        assets,
        showAssetsWithoutDefinitions ? (options.externalAssets ?? []) : [],
        showStubAssets,
      ),
    [assets, showStubAssets, showAssetsWithoutDefinitions, options.externalAssets],
  );

  const [fullAssetGraphData, setFullAssetGraphData] = useState<GraphData | null>(null);
  useBlockTraceUntilTrue('FullAssetGraphData', !!fullAssetGraphData);

  useEffect(() => {
    if (options.loading) {
      return;
    }
    const data = buildGraphData(allNodes);
    setFullAssetGraphData(data);
  }, [allNodes, options.loading]);

  return {fullAssetGraphData, loading: loading || !!options.loading};
}

export type GraphDataState = {
  graphAssetKeys: AssetKey[];
  allAssetKeys: AssetKey[];
  assetGraphData: GraphData | null;
};
const INITIAL_STATE: GraphDataState = {
  graphAssetKeys: [],
  allAssetKeys: [],
  assetGraphData: null,
};

/** Fetches data for doing asset selection filtering in the asset catalog and asset graph:
 *
 * @param pipelineSelector: Optionally scope to an asset job, or pass null for the global graph
 *
 * @param opsQuery: filter the returned graph using selector syntax string (eg: asset_name++)
 *
 * @param filterNodes: filter the returned graph using the provided function. The global graph
 * uses this option to implement the "3 of 4 repositories" picker.
 */
export function useAssetGraphData(opsQuery: string, options: AssetGraphFetchScope) {
  const {showStubAssets} = useShowStubAssets();
  const {showAssetsWithoutDefinitions} = useShowAssetsWithoutDefinitions();
  const {assets, loading: assetsLoading} = useAllAssetsNodes();

  const allNodes = useMemo(
    () =>
      getAllAssets(
        assets,
        showAssetsWithoutDefinitions ? (options.externalAssets ?? []) : [],
        showStubAssets,
      ),
    [assets, options.externalAssets, showAssetsWithoutDefinitions, showStubAssets],
  );

  const {pipelineSelector, groupSelector, hideNodesMatching} = options;

  const repoFilteredNodes = useMemo(() => {
    let matching = allNodes;
    if (pipelineSelector) {
      matching = matching.filter((node) => {
        return (
          node.jobNames.includes(pipelineSelector.pipelineName) &&
          node.repository.name === pipelineSelector.repositoryName &&
          node.repository.location.name === pipelineSelector.repositoryLocationName
        );
      });
    }
    if (groupSelector) {
      matching = matching.filter((node) => {
        return (
          node.groupName === groupSelector.groupName &&
          node.repository.name === groupSelector.repositoryName &&
          node.repository.location.name === groupSelector.repositoryLocationName
        );
      });
    }
    if (hideNodesMatching) {
      matching = reject(matching, hideNodesMatching);
    }
    return matching;
  }, [allNodes, pipelineSelector, groupSelector, hideNodesMatching]);

  const graphQueryItems = useMemo(
    () => buildGraphQueryItems(repoFilteredNodes),
    [repoFilteredNodes],
  );

  const [state, setState] = useState<GraphDataState>(INITIAL_STATE);

  const {kinds, hideEdgesToNodesOutsideQuery} = options;

  const {loading: supplementaryDataLoading, data: supplementaryData} =
    useAssetGraphSupplementaryData(opsQuery, allNodes);

  useLayoutEffect(() => {
    if (options.loading || supplementaryDataLoading || assetsLoading || options.skip) {
      return;
    }

    if (repoFilteredNodes === undefined || graphQueryItems === undefined) {
      setState({allAssetKeys: [], graphAssetKeys: [], assetGraphData: null});
      return;
    }

    const data = computeGraphData({
      repoFilteredNodes,
      graphQueryItems,
      opsQuery,
      kinds,
      hideEdgesToNodesOutsideQuery,
      supplementaryData,
    });
    setState(data);
  }, [
    repoFilteredNodes,
    graphQueryItems,
    opsQuery,
    kinds,
    hideEdgesToNodesOutsideQuery,
    options.loading,
    supplementaryData,
    supplementaryDataLoading,
    options.skip,
    assetsLoading,
  ]);

  const loading =
    !options.skip && (assetsLoading || !!supplementaryDataLoading || !!options.loading);
  useBlockTraceUntilTrue('useAssetGraphData', !loading);
  return {
    loading,
    assetGraphData: state.assetGraphData,
    graphQueryItems,
    graphAssetKeys: state.graphAssetKeys,
    allAssetKeys: state.allAssetKeys,
  };
}

const buildGraphQueryItems = (nodes: AssetNode[]) => {
  const items: {[name: string]: AssetGraphQueryItem} = {};

  for (const node of nodes) {
    const name = tokenForAssetKey(node.assetKey);
    items[name] = {
      node,
      name,
      inputs: node.dependencyKeys.map((key) => ({
        dependsOn: [{solid: {name: tokenForAssetKey(key)}}],
      })),
      outputs: node.dependedByKeys.map((key) => ({
        dependedBy: [{solid: {name: tokenForAssetKey(key)}}],
      })),
    };
  }
  return Object.values(items);
};

export const calculateGraphDistances = (items: GraphQueryItem[], assetKey: AssetKey) => {
  const map = new Map(items.map((g) => [g.name, g]));
  const start = map.get(tokenForAssetKey(assetKey));
  if (!start) {
    return {upstream: 0, downstream: 0};
  }

  let upstreamDepth = -1;
  let candidates = new Set([start.name]);
  const visitedUpstream = new Set<string>();

  while (candidates.size > 0) {
    const nextCandidates: Set<string> = new Set();
    upstreamDepth += 1;

    candidates.forEach((candidate) => {
      visitedUpstream.add(candidate);
      const inputs = map.get(candidate)?.inputs ?? [];
      inputs.forEach((i) =>
        i.dependsOn.forEach((d) => {
          if (!visitedUpstream.has(d.solid.name) && !candidates.has(d.solid.name)) {
            nextCandidates.add(d.solid.name);
          }
        }),
      );
    });
    candidates = nextCandidates;
  }

  let downstreamDepth = -1;
  candidates = new Set([start.name]);
  const visitedDownstream = new Set<string>();

  while (candidates.size > 0) {
    const nextCandidates: Set<string> = new Set();
    downstreamDepth += 1;

    candidates.forEach((candidate) => {
      visitedDownstream.add(candidate);
      const outputs = map.get(candidate)?.outputs ?? [];
      outputs.forEach((i) =>
        i.dependedBy.forEach((d) => {
          if (!visitedDownstream.has(d.solid.name) && !candidates.has(d.solid.name)) {
            nextCandidates.add(d.solid.name);
          }
        }),
      );
    });
    candidates = nextCandidates;
  }

  return {
    upstream: upstreamDepth,
    downstream: downstreamDepth,
  };
};

const buildExternalAssetQueryItem = (asset: {
  id: string;
  key: {path: string[]};
}): WorkspaceAssetFragment => {
  return {
    __typename: 'AssetNode',
    changedReasons: [],
    kinds: [],
    hasMaterializePermission: false,
    graphName: '',
    opVersion: null,
    hasAssetChecks: false,
    hasReportRunlessAssetEventPermission: false,
    pools: [],
    internalFreshnessPolicy: null,
    partitionDefinition: null,
    automationCondition: null,
    isMaterializable: false,
    isAutoCreatedStub: true,
    tags: [],
    owners: [],
    id: asset.id,
    groupName: '',
    isExecutable: false,
    isPartitioned: false,
    opNames: [],
    jobNames: [],
    computeKind: null,
    isObservable: false,
    description: null,
    repository: {
      __typename: 'Repository',
      id: '',
      name: '',
      location: {
        __typename: 'RepositoryLocation',
        id: '',
        name: '',
      },
    },
    assetKey: {
      __typename: 'AssetKey',
      ...asset.key,
    },
    dependencyKeys: [],
    dependedByKeys: [],
  };
};

const getAllAssets = weakMapMemoize(
  (
    sdas: ReturnType<typeof useAllAssetsNodes>['assets'],
    externalAssets: {id: string; key: {path: Array<string>}}[],
    showStubAssets: boolean,
  ) => {
    return [
      ...sdas.map((sda) => sda.definition).filter((d) => showStubAssets || !d?.isAutoCreatedStub),
      ...externalAssets.map((a) => buildExternalAssetQueryItem(a)),
    ];
  },
);

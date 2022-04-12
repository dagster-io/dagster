import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {filterByQuery, GraphQueryItem} from '../../app/GraphQueryImpl';
import {tokenForAssetKey} from '../../app/Util';
import {PipelineSelector} from '../../types/globalTypes';

import {ASSET_NODE_FRAGMENT} from './AssetNode';
import {buildGraphData} from './Utils';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQuery_assetNodes,
} from './types/AssetGraphQuery';

/** Fetches data for rendering an asset graph:
 *
 * @param pipelineSelector: Optionally scope to an asset job, or pass null for the global graph
 *
 * @param opsQuery: filter the returned graph using selector syntax string (eg: asset_name++)
 *
 * @param filterNodes: filter the returned graph using the provided function. The global graph
 * uses this option to implement the "3 of 4 repositories" picker.
 */
export function useAssetGraphData(
  pipelineSelector: PipelineSelector | null | undefined,
  opsQuery: string,
  filterNodes?: (assetNode: AssetGraphQuery_assetNodes) => boolean,
) {
  const fetchResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSET_GRAPH_QUERY, {
    variables: {pipelineSelector},
    notifyOnNetworkStatusChange: true,
  });

  const fetchResultFilteredNodes = React.useMemo(() => {
    const nodes = fetchResult.data?.assetNodes;
    if (!nodes) {
      return undefined;
    }
    return filterNodes ? nodes.filter(filterNodes) : nodes;
  }, [fetchResult.data, filterNodes]);

  const {
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    applyingEmptyDefault,
  } = React.useMemo(() => {
    if (fetchResultFilteredNodes === undefined) {
      return {
        graphAssetKeys: [],
        graphQueryItems: [],
        assetGraphData: null,
        applyingEmptyDefault: false,
      };
    }
    const graphQueryItems = buildGraphQueryItems(fetchResultFilteredNodes);
    const {all, applyingEmptyDefault} = filterByQuery(graphQueryItems, opsQuery);

    return {
      graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
      assetGraphData: buildGraphData(all.map((n) => n.node)),
      graphQueryItems,
      applyingEmptyDefault,
    };
  }, [fetchResultFilteredNodes, opsQuery]);

  return {
    fetchResult,
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    applyingEmptyDefault,
  };
}

type AssetNode = AssetGraphQuery_assetNodes;

const buildGraphQueryItems = (nodes: AssetNode[]) => {
  const items: {
    [name: string]: GraphQueryItem & {
      node: AssetNode;
    };
  } = {};

  for (const node of nodes) {
    const name = tokenForAssetKey(node.assetKey);
    items[name] = {
      node: node,
      name: name,
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

const ASSET_GRAPH_QUERY = gql`
  query AssetGraphQuery($pipelineSelector: PipelineSelector) {
    assetNodes(pipeline: $pipelineSelector) {
      id
      ...AssetNodeFragment
      jobNames
      dependencyKeys {
        path
      }
      dependedByKeys {
        path
      }
    }
  }
  ${ASSET_NODE_FRAGMENT}
`;

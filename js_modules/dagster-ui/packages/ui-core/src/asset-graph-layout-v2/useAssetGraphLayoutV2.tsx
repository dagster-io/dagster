import {useLayoutEffect, useMemo, useRef, useState} from 'react';

import {NodeType} from './common/ModelGraph';
import {
  ProcessGraphRequest,
  ProcessGraphResponse,
  UpdateExpandedGroupsRequest,
  UpdateExpandedGroupsResponse,
  WorkerEvent,
  WorkerEventType,
} from './common/WorkerEvents';
import {isNodeExpanded} from './common/utils';
import {GraphData} from '../asset-graph/Utils';
import {
  AssetGraphLayout,
  AssetLayout,
  GroupLayout,
  LayoutAssetGraphOptions,
} from '../asset-graph/layout';

class AssetGraphLayoutWorker {
  private requestId: number = 0;
  private callbacksByRequestId: {[key: number]: (response: WorkerEvent) => void} = {};
  private static _instance: AssetGraphLayoutWorker;
  public static getInstance() {
    if (!this._instance) {
      this._instance = new AssetGraphLayoutWorker();
    }
    return this._instance;
  }

  private worker: Worker;
  private constructor() {
    this.worker = new Worker(new URL('./worker/AssetGraphLayoutV2.worker', import.meta.url));
    this.worker.addEventListener('message', (event) => {
      const data = event.data as WorkerEvent;
      const cb = this.callbacksByRequestId[data.requestId];
      if (!cb) {
        // Handle invalid state;
        return;
      }
      switch (data.eventType) {
        case WorkerEventType.PROCESS_GRAPH_RESP:
        case WorkerEventType.UPDATE_EXPANDED_GROUPS_RESP:
          cb(data);
          return;
      }
    });
  }

  public async processGraph(
    graphId: string,
    graph: GraphData,
    expandedGroups: string[],
    options: LayoutAssetGraphOptions,
  ) {
    const processGraphRequest: ProcessGraphRequest = {
      requestId: this.requestId++,
      eventType: WorkerEventType.PROCESS_GRAPH_REQ,
      graph,
      graphId,
      targetDeepestGroupNodeIdsToExpand: expandedGroups,
      options,
    };
    return await this.sendRequest(processGraphRequest);
  }
  public async updateExpandedGroups(
    graphId: string,
    expandedGroups: string[],
    options: LayoutAssetGraphOptions,
  ) {
    const updateExpandedGroupsRequest: UpdateExpandedGroupsRequest = {
      requestId: this.requestId++,
      eventType: WorkerEventType.UPDATE_EXPANDED_GROUPS_REQ,
      graphId,
      targetDeepestGroupNodeIdsToExpand: expandedGroups,
      options,
    };
    return await this.sendRequest(updateExpandedGroupsRequest);
  }

  private async sendRequest(data: WorkerEvent) {
    console.log('send request', data);
    let resp: WorkerEvent;
    await new Promise((res) => {
      const requestId = data.requestId;
      this.callbacksByRequestId[requestId] = (response: WorkerEvent) => {
        resp = response;
        res(0);
      };
      console.log('posting', data);
      this.worker.postMessage(data);
    });
    console.log('response', resp!);
    return resp!;
  }
}

export function useAssetGraphLayout(
  graphData: GraphData,
  expandedGroups: string[],
  opts: LayoutAssetGraphOptions,
) {
  const worker = AssetGraphLayoutWorker.getInstance();
  const graphId = useMemo(() => computeGraphId(graphData), [graphData]);
  const previousGraphId = useRef('');

  const [layoutResponse, setLayoutResponse] = useState<
    ProcessGraphResponse | UpdateExpandedGroupsResponse | null
  >();
  const [loading, setLoading] = useState(true);
  const layout = useMemo(() => {
    if (!layoutResponse) {
      return null;
    }
    const layout = convertToAssetGraphLayout(layoutResponse);
    return layout;
  }, [layoutResponse]);

  useLayoutEffect(() => {
    async function handleUpdate() {
      const isNewGraph = graphId !== previousGraphId.current;
      previousGraphId.current = graphId;
      setLoading(true);
      let response: ProcessGraphResponse | UpdateExpandedGroupsResponse;
      if (isNewGraph) {
        response = (await worker.processGraph(
          graphId,
          graphData,
          expandedGroups,
          opts,
        )) as ProcessGraphResponse;
      } else {
        response = (await worker.updateExpandedGroups(
          graphId,
          expandedGroups,
          opts,
        )) as UpdateExpandedGroupsResponse;
      }
      setLayoutResponse(response);
      setLoading(false);
    }
    handleUpdate();
  }, [graphId, worker, expandedGroups, graphData, opts]);

  return {
    loading,
    async: true,
    layout,
  };
}

function computeGraphId(graphData: GraphData) {
  // Make the cache key deterministic by alphabetically sorting all of the keys since the order
  // of the keys is not guaranteed to be consistent even when the graph hasn't changed.
  function recreateObjectWithKeysSorted(obj: Record<string, Record<string, boolean>>) {
    const newObj: Record<string, Record<string, boolean>> = {};
    Object.keys(obj)
      .sort()
      .forEach((key) => {
        newObj[key] = Object.keys(obj[key]!)
          .sort()
          .reduce(
            (acc, k) => {
              acc[k] = obj[key]![k]!;
              return acc;
            },
            {} as Record<string, boolean>,
          );
      });
    return newObj;
  }

  return simpleHash(
    JSON.stringify({
      downstream: recreateObjectWithKeysSorted(graphData.downstream),
      upstream: recreateObjectWithKeysSorted(graphData.upstream),
      nodes: Object.keys(graphData.nodes)
        .sort()
        .map((key) => graphData.nodes[key]),
    }),
  );
}

function simpleHash(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36); // Convert to base36 for a shorter representation
}

function convertToAssetGraphLayout(
  response: ProcessGraphResponse | UpdateExpandedGroupsResponse,
): AssetGraphLayout {
  const graph = response.modelGraph;
  const nodes: {[id: string]: AssetLayout} = {};
  const groups: {[id: string]: GroupLayout} = {};

  let maxWidth = 0;
  let maxHeight = 0;

  // Process nodes
  for (const node of graph.nodes) {
    const {id, width = 0, height = 0} = node;
    if (!('x' in node) || !('y' in node)) {
      // This means the node is not included in the layout
      // because the group containing it is not expanded.
      continue;
    }
    const x = node.globalX ?? node.x ?? 0;
    const y = node.globalY ?? node.y ?? 0;

    // Calculate bounds
    const bounds = {
      x,
      y,
      width,
      height,
    };

    if (width !== 0 && height !== 0) {
      if (node.nodeType === NodeType.GROUP_NODE) {
        groups[id] = {
          id,
          groupName: node.groupName,
          repositoryName: node.repositoryName,
          repositoryLocationName: node.repositoryLocationName,
          bounds,
          expanded: node.expanded,
        };
      } else if (isNodeExpanded(node.id, response.modelGraph)) {
        nodes[id] = {id, bounds};
      }
    }

    if (node.nodeType !== NodeType.ASSET_NODE) {
      maxWidth = Math.max(maxWidth, x + width / 2);
      maxHeight = Math.max(maxHeight, y + height / 2);
    }
  }

  return {
    width: maxWidth,
    height: maxHeight,
    edges: Object.values(response.modelGraph.edgesByGroupNodeIds).flat(),
    nodes,
    groups,
  };
}

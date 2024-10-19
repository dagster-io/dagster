import {LayoutAssetGraphOptions} from './GraphConfig';
import {GraphExpander} from './GraphExpander';
import {GraphLayout} from './GraphLayout';
import {GraphProcessor} from './GraphProcessor';
import {GraphData} from '../../asset-graph/Utils';
import {ModelGraph} from '../common/ModelGraph';
import {
  ProcessGraphResponse,
  UpdateExpandedGroupsResponse,
  WorkerEvent,
  WorkerEventType,
} from '../common/WorkerEvents';

const MODEL_GRAPHS_CACHE: Record<string, ModelGraph> = {};

self.addEventListener('message', (event) => {
  const workerEvent = event.data as WorkerEvent;
  switch (workerEvent.eventType) {
    // Handle processing input graph.
    case WorkerEventType.PROCESS_GRAPH_REQ: {
      const modelGraph = handleProcessGraph(
        workerEvent.graph,
        workerEvent.targetDeepestGroupNodeIdsToExpand,
        workerEvent.options,
      );
      cacheModelGraph(modelGraph, workerEvent.graphId);
      const resp: ProcessGraphResponse = {
        requestId: workerEvent.requestId,
        eventType: WorkerEventType.PROCESS_GRAPH_RESP,
        modelGraph,
        graphId: workerEvent.graphId,
      };
      postMessage(resp);
      break;
    }
    case WorkerEventType.UPDATE_EXPANDED_GROUPS_REQ: {
      const modelGraph = getCachedModelGraph(workerEvent.graphId);
      handleUpdateExpandedGroups(
        modelGraph,
        workerEvent.targetDeepestGroupNodeIdsToExpand,
        workerEvent.options,
      );
      cacheModelGraph(modelGraph, workerEvent.graphId);
      const resp: UpdateExpandedGroupsResponse = {
        requestId: workerEvent.requestId,
        eventType: WorkerEventType.UPDATE_EXPANDED_GROUPS_RESP,
        modelGraph,
      };
      postMessage(resp);
      break;
    }
    default:
      break;
  }
});

function handleProcessGraph(
  graph: GraphData,
  targetDeepestGroupNodeIdsToExpand: string[],
  options: LayoutAssetGraphOptions,
): ModelGraph {
  let error: string | undefined = undefined;

  // Processes the given input graph `Graph` into a `ModelGraph`.
  const processor = new GraphProcessor(graph);
  const modelGraph = processor.process();

  // Check nodes with empty ids.
  if (modelGraph.nodesById[''] != null) {
    error =
      'Some nodes have empty strings as ids which will cause layout failures. See console for details.';
    console.warn('Nodes with empty ids', modelGraph.nodesById['']);
  }

  if (!error) {
    if (targetDeepestGroupNodeIdsToExpand.length) {
      handleUpdateExpandedGroups(modelGraph, targetDeepestGroupNodeIdsToExpand, options);
    } else {
      const layout = new GraphLayout(modelGraph, options);
      try {
        layout.layout();
      } catch (e) {
        error = `Failed to layout graph: ${e}`;
      }
    }
  }
  return modelGraph;
}

function handleUpdateExpandedGroups(
  modelGraph: ModelGraph,
  targetDeepestGroupNodeIdsToExpand: string[],
  options: LayoutAssetGraphOptions,
) {
  const expander = new GraphExpander(modelGraph, options);
  expander.reLayoutGraph(targetDeepestGroupNodeIdsToExpand, true);
}

function cacheModelGraph(modelGraph: ModelGraph, id: string) {
  MODEL_GRAPHS_CACHE[id] = modelGraph;
}

function getCachedModelGraph(graphId: string): ModelGraph {
  const cachedModelGraph = MODEL_GRAPHS_CACHE[graphId];
  if (cachedModelGraph == null) {
    throw new Error(`ModelGraph with id "${graphId}" not found"`);
  }
  return cachedModelGraph;
}

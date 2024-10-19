import * as dagre from 'dagre';

import {LayoutAssetGraphOptions} from './GraphConfig';
import {GraphLayout} from './GraphLayout';
import {GroupNode, ModelGraph} from '../common/ModelGraph';
import {LAYOUT_MARGIN_X} from '../common/conts';
import {Rect} from '../common/types';
import {getDeepestExpandedGroupNodeIds, isGroupNode} from '../common/utils';

/**
 * A class that handles expanding and collapsing group nodes in a model graph.
 */
export class GraphExpander {
  /** This is for testing purpose. */
  readonly dagreGraphs: dagre.graphlib.Graph[] = [];

  constructor(
    private readonly modelGraph: ModelGraph,
    private readonly options: LayoutAssetGraphOptions,
  ) {}

  /** Expands from the given deepest group nodes back to root. */
  expandFromDeepestGroupNodes(groupNodeIds: string[]) {
    // Get all ancestors from the given group node ids.
    const seenGroupNodeIds = new Set<string>();
    const queue: string[] = [...groupNodeIds];
    while (queue.length > 0) {
      const curGroupNodeId = queue.shift()!;
      if (seenGroupNodeIds.has(curGroupNodeId)) {
        continue;
      }
      const groupNode = this.modelGraph.nodesById[curGroupNodeId] as GroupNode;
      if (!groupNode) {
        continue;
      }
      seenGroupNodeIds.add(curGroupNodeId);
      const parentGroupNodeId = groupNode?.parentId;
      if (parentGroupNodeId) {
        queue.push(parentGroupNodeId);
      }
    }

    // Sort them by level in descending order.
    const sortedGroupNodeIds = Array.from(seenGroupNodeIds).sort((a, b) => {
      const nodeA = this.modelGraph.nodesById[a]!;
      const nodeB = this.modelGraph.nodesById[b]!;
      return nodeB.level - nodeA.level;
    });

    // Layout group nodes in this sorted list.
    for (const groupNodeId of sortedGroupNodeIds) {
      const groupNode = this.modelGraph.nodesById[groupNodeId] as GroupNode;
      if (!groupNode) {
        continue;
      }
      groupNode.expanded = true;

      // Layout children.
      const layout = new GraphLayout(this.modelGraph, this.options);
      const rect = layout.layout(groupNodeId);

      // Grow size.
      const curTargetWidth = rect.width + LAYOUT_MARGIN_X * 2;
      const curTargetHeight = this.getTargetGroupNodeHeight(rect, groupNode);
      groupNode.width = curTargetWidth;
      groupNode.height = curTargetHeight;
    }

    // Layout the root level nodes.
    const layout = new GraphLayout(this.modelGraph, this.options);
    const rootRect = layout.layout();
    // TODO (salazarm) use the root rect? Add dimensions to ModelGraph?
    console.log({rootRect});

    // From root, update offsets of all nodes that have x, y set (meaning they
    // have the layout data).
    for (const node of this.modelGraph.rootNodes) {
      if (isGroupNode(node)) {
        this.updateNodeOffset(node);
      }
    }
  }

  /**
   * Uses the current collapse/expand states of the group nodes and re-lays out
   * the entire graph.
   */
  reLayoutGraph(
    targetDeepestGroupNodeIdsToExpand?: string[],
    clearAllExpandStates?: boolean,
  ): string[] {
    let curTargetDeepestGroupNodeIdsToExpand: string[] | undefined =
      targetDeepestGroupNodeIdsToExpand;
    if (!curTargetDeepestGroupNodeIdsToExpand) {
      // Find the deepest group nodes that non of its child group nodes is
      // expanded.
      const deepestExpandedGroupNodeIds: string[] = [];
      this.clearLayoutData(undefined);
      getDeepestExpandedGroupNodeIds(undefined, this.modelGraph, deepestExpandedGroupNodeIds);
      curTargetDeepestGroupNodeIdsToExpand = deepestExpandedGroupNodeIds;
    } else {
      if (clearAllExpandStates) {
        this.clearLayoutData(undefined, true);
      }
    }

    // Expand those nodes one by one.
    if (curTargetDeepestGroupNodeIdsToExpand.length > 0) {
      this.expandFromDeepestGroupNodes(curTargetDeepestGroupNodeIdsToExpand);
    } else {
      const layout = new GraphLayout(this.modelGraph, this.options);
      layout.layout();
    }

    return curTargetDeepestGroupNodeIdsToExpand;
  }

  private updateNodeOffset(groupNode: GroupNode) {
    if (!groupNode.expanded) {
      return;
    }
    for (const nodeId of groupNode.childrenIds || []) {
      const node = this.modelGraph.nodesById[nodeId]!;
      if (node.x != null && node.y != null) {
        node.globalX = (node.x || 0) + (groupNode.globalX || 0);
        node.globalY = (node.y || 0) + (groupNode.globalY || 0);
      }
      if (isGroupNode(node)) {
        this.updateNodeOffset(node);
      }
    }
  }

  private clearLayoutData(root: GroupNode | undefined, clearAllExpandStates?: boolean) {
    let childrenIds: string[] = [];
    if (root == null) {
      childrenIds = this.modelGraph.rootNodes.map((node) => node.id);
    } else {
      childrenIds = root.childrenIds || [];
    }
    if (clearAllExpandStates && root != null) {
      root.expanded = false;
      delete this.modelGraph.edgesByGroupNodeIds[root.id];
    }
    for (const childNodeId of childrenIds) {
      const childNode = this.modelGraph.nodesById[childNodeId];
      if (!childNode || !isGroupNode(childNode)) {
        continue;
      }
      childNode.width = undefined;
      childNode.height = undefined;
      if (isGroupNode(childNode) && childNode.expanded) {
        this.clearLayoutData(childNode, clearAllExpandStates);
      }
    }
  }

  private getTargetGroupNodeHeight(rect: Rect, _groupNode: GroupNode): number {
    return rect.height;
  }
}

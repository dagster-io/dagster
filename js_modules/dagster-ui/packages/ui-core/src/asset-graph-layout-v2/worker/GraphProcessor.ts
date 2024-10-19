import {getLayoutGraph} from './GraphLayout';
import {GraphData, groupIdForNode} from '../../asset-graph/Utils';
import {
  LayoutAssetGraphOptions,
  getAssetLinkDimensions,
  getAssetNodeDimensions,
} from '../../asset-graph/layout';
import {
  AssetLinkNode,
  AssetNode,
  GroupNode,
  ModelGraph,
  ModelNode,
  NodeType,
} from '../common/ModelGraph';
import {DEFAULT_GROUP_NODE_CHILDREN_COUNT_THRESHOLD} from '../common/conts';
import {Edge} from '../common/types';
import {findCommonNamespace, isGroupNode} from '../common/utils';

/**
 * A class that processes given `GraphData` into a `ModelGraph`.
 */
export class GraphProcessor {
  constructor(
    private readonly graph: GraphData,
    private readonly groupNodeChildrenCountThreshold = DEFAULT_GROUP_NODE_CHILDREN_COUNT_THRESHOLD,
    private readonly options: LayoutAssetGraphOptions = {direction: 'horizontal'},
  ) {}

  process(): ModelGraph {
    const modelGraph = this.createEmptyModelGraph();

    this.processNodes(modelGraph);

    this.processEdgeRelationships(modelGraph);

    this.processNamespaceRelationships(modelGraph);

    this.generateLayoutGraphConnections(modelGraph);

    this.splitLargeGroupNodes(modelGraph);
    return modelGraph;
  }

  /**
   * Scans nodes in `Graph` and creates the corresponding `AssetNode` and
   * `GroupNode` in the `ModelGraph` (see model_graph.ts for more details).
   */
  processNodes(modelGraph: ModelGraph) {
    const seenGroups = new Set<string>();
    const groups: GroupNode[] = [];
    const seenNodes = new Set<string>();

    const allNodes = new Set<string>();

    for (const graphNode of Object.values(this.graph.nodes)) {
      seenNodes.add(graphNode.id);
      const group = groupIdForNode(graphNode);
      const {width, height} = getAssetNodeDimensions(graphNode.definition);
      const assetNode: AssetNode = {
        nodeType: NodeType.ASSET_NODE,
        ...graphNode,
        parentId: group,
        level: 1,
        width,
        height,
        namespace: `${group}/${graphNode.id}`,
      };
      modelGraph.nodes.push(assetNode);
      modelGraph.nodesById[assetNode.id] = assetNode;

      Object.keys(this.graph.downstream[assetNode.id] ?? {}).forEach((downstreamNodeId) => {
        allNodes.add(downstreamNodeId);
      });
      Object.keys(this.graph.upstream[assetNode.id] ?? {}).forEach((upstreamNodeId) => {
        allNodes.add(upstreamNodeId);
      });

      if (!seenGroups.has(group)) {
        const groupNode: GroupNode = {
          nodeType: NodeType.GROUP_NODE,
          groupName: graphNode.definition.groupName,
          repositoryName: graphNode.definition.repository.name,
          repositoryLocationName: graphNode.definition.repository.location.name,
          id: group,
          level: 0,
          expanded: false,
          namespace: group,
        };
        groups.push(groupNode);
        seenGroups.add(group);
      }
    }
    if (groups.length > 1) {
      // Only add group nodes if theres more than 1 group
      groups.forEach((groupNode) => {
        modelGraph.nodes.push(groupNode);
        modelGraph.nodesById[groupNode.id] = groupNode;
      });
    } else {
      // remove the parentId
      modelGraph.nodes.forEach((node) => {
        node.parentId = undefined;
        node.level = 0;
      });
    }
    // Add link nodes.
    Array.from(allNodes).forEach((nodeId) => {
      if (seenNodes.has(nodeId)) {
        return;
      }
      const {width, height} = getAssetLinkDimensions(nodeId, this.options);
      const assetNode: AssetLinkNode = {
        nodeType: NodeType.ASSET_LINK_NODE,
        id: nodeId,
        level: 0,
        width,
        height,
        namespace: nodeId,
      };
      modelGraph.nodes.push(assetNode);
      modelGraph.nodesById[assetNode.id] = assetNode;
    });
  }

  /**
   * Sets edges in the given model graph based on the edges in the input graph.
   */
  processEdgeRelationships(modelGraph: ModelGraph) {
    for (const nodeId of Object.keys(modelGraph.nodesById)) {
      const node = modelGraph.nodesById[nodeId] as AssetNode;
      if (!node) {
        console.log('missing node', nodeId);
        continue;
      }

      const upstreamEdges = Object.keys(this.graph.upstream[nodeId] || {}) || [];

      // From the graph node's incoming edges, populate the incoming and
      // outgoing edges for the corresponding node in the model graph.
      for (const sourceNodeId of upstreamEdges) {
        const incomingEdge: Edge = {
          sourceNodeId,
          targetNodeId: nodeId,
        };
        const sourceNode = modelGraph.nodesById[sourceNodeId] as AssetNode;
        if (!sourceNode) {
          console.log('Missing source node', sourceNode);
          continue;
        }

        // Incoming edges.
        if (node.upstreamEdges == null) {
          node.upstreamEdges = [];
        }
        if (node.upstreamEdges.find((edge) => edge.sourceNodeId === sourceNodeId) == null) {
          node.upstreamEdges.push({...incomingEdge});
        }

        // Outgoing edges.
        if (sourceNode.downstreamEdges == null) {
          sourceNode.downstreamEdges = [];
        }
        if (sourceNode.downstreamEdges.find((edge) => edge.targetNodeId === node.id) == null) {
          sourceNode.downstreamEdges.push({
            targetNodeId: node.id,
            sourceNodeId: incomingEdge.sourceNodeId,
          });
        }
      }
    }
  }

  /**
   * Sets namespace relationships in model graph based on the hierarchy data
   * stored in input node's `namespace`.
   */
  processNamespaceRelationships(modelGraph: ModelGraph) {
    for (const node of modelGraph.nodes) {
      // Root node.
      if (node.level === 0) {
        modelGraph.rootNodes.push(node);
        continue;
      }

      // Set namespace parent.
      const parentNodeId = node.parentId!;
      const parentGroupNode = modelGraph.nodesById[parentNodeId] as GroupNode;

      // Set namespace children.
      if (parentGroupNode) {
        if (parentGroupNode.childrenIds == null) {
          parentGroupNode.childrenIds = [];
        }
        if (!parentGroupNode.childrenIds.includes(node.id)) {
          parentGroupNode.childrenIds.push(node.id);
        }
      }
    }
  }

  /**
   * Generates layout graph connections for the given model graph.
   * TODO (salazarm): Validate this function is legit.
   */
  generateLayoutGraphConnections(modelGraph: ModelGraph) {
    modelGraph.layoutGraphEdges = {};

    // Find all op nodes that don't have incoming edges.
    const assetNodesWithoutIncomingEdges: Array<AssetNode | AssetLinkNode> = [];
    for (const node of modelGraph.nodes) {
      if (isGroupNode(node)) {
        continue;
      }
      const filteredIncomingEdges = node.upstreamEdges || [];
      if (filteredIncomingEdges.length === 0) {
        assetNodesWithoutIncomingEdges.push(node);
      }
    }

    // Do a BFS from assetNodesWithoutIncomingEdges.
    const queue = [...assetNodesWithoutIncomingEdges];
    const seenNodeIds = new Set<string>();
    while (queue.length > 0) {
      const curNode = queue.shift();
      if (curNode == null) {
        continue;
      }
      if (seenNodeIds.has(curNode.id)) {
        continue;
      }
      seenNodeIds.add(curNode.id);

      const downstreamEdges = curNode.downstreamEdges || [];
      for (const edge of downstreamEdges) {
        const targetNode = modelGraph.nodesById[edge.targetNodeId] as AssetNode | AssetLinkNode;
        const commonNs = findCommonNamespace(curNode.namespace, targetNode.namespace);

        const commonNsGroupId = commonNs === '' ? '' : `${commonNs}`;
        if (modelGraph.layoutGraphEdges[commonNsGroupId] == null) {
          modelGraph.layoutGraphEdges[commonNsGroupId] = {};
        }
        if (modelGraph.layoutGraphEdges[commonNsGroupId][curNode.id] == null) {
          modelGraph.layoutGraphEdges[commonNsGroupId][curNode.id] = {};
        }
        modelGraph.layoutGraphEdges[commonNsGroupId]![curNode.id]![targetNode.id] = true;
      }
      for (const edge of downstreamEdges) {
        const targetNode = modelGraph.nodesById[edge.targetNodeId] as AssetNode;
        queue.push(targetNode);
      }
    }
  }

  /**
   * Finds group nodes with a large number of children, and splits them into
   * different groups
   */
  splitLargeGroupNodes(modelGraph: ModelGraph) {
    // From root, do a BFS search on all group nodes.
    const queue: Array<GroupNode | undefined> = [undefined];
    let hasLargeGroupNodes = false;
    while (queue.length > 0) {
      const curGroupNode = queue.shift();
      let children: ModelNode[] =
        curGroupNode == null
          ? modelGraph.rootNodes
          : (curGroupNode.childrenIds || []).map((id) => modelGraph.nodesById[id]!);

      // Split the group node if its child count is over the threshold.
      if (children.length > this.groupNodeChildrenCountThreshold) {
        hasLargeGroupNodes = true;
        const layoutGraph = getLayoutGraph(curGroupNode?.id || '', children, modelGraph);

        // Find root nodes of the layout graph.
        const rootNodes: ModelNode[] = [];
        for (const nodeId of Object.keys(layoutGraph.nodes)) {
          if (layoutGraph.upstreamEdges[nodeId] == null) {
            rootNodes.push(modelGraph.nodesById[nodeId]!);
          }
        }

        // Do a DFS from the layout graph root nodes. Create a new group
        // whenever the node counts reaches the threshold.
        const groups: ModelNode[][] = [];
        let curGroup: ModelNode[] = [];
        const visitedNodeIds = new Set<string>();
        const visit = (curNodeId: string) => {
          if (visitedNodeIds.has(curNodeId)) {
            return;
          }
          visitedNodeIds.add(curNodeId);
          const node = modelGraph.nodesById[curNodeId]!;
          curGroup.push(node);
          if (curGroup.length === this.groupNodeChildrenCountThreshold) {
            groups.push(curGroup);
            curGroup = [];
          }
          for (const childId of layoutGraph.downstreamEdges[node.id] || []) {
            visit(childId);
          }
        };
        for (const rootNode of rootNodes) {
          visit(rootNode.id);
        }
        if (curGroup.length < this.groupNodeChildrenCountThreshold && curGroup.length > 0) {
          groups.push(curGroup);
        }

        // Create a new group node for each group.
        const newGroupNodes: GroupNode[] = [];
        for (let groupIndex = 0; groupIndex < groups.length; groupIndex++) {
          const nodes = groups[groupIndex]!;
          const newGroupNodeNamespace =
            curGroupNode == null ? '' : `${curGroupNode.namespace}/${curGroupNode.id}`;
          const baseId = `section_${groupIndex + 1}_of_${groups.length}`;
          const newGroupNodeId = `${baseId}`;
          const newGroupNode: GroupNode = {
            nodeType: NodeType.GROUP_NODE,
            id: newGroupNodeId,
            namespace: newGroupNodeNamespace,
            groupName: curGroupNode?.groupName ?? '',
            repositoryName: curGroupNode?.repositoryLocationName ?? '',
            repositoryLocationName: curGroupNode?.repositoryLocationName ?? '',
            level: 0,
            parentId: curGroupNode?.id,
            childrenIds: nodes.map((node) => node.id),
            expanded: false,
            sectionContainer: true,
          };
          newGroupNodes.push(newGroupNode);

          // Add the new group node to the model graph.
          modelGraph.nodes.push(newGroupNode);
          modelGraph.nodesById[newGroupNode.id] = newGroupNode;
          if (modelGraph.artificialGroupNodeIds == null) {
            modelGraph.artificialGroupNodeIds = [];
          }
          modelGraph.artificialGroupNodeIds.push(newGroupNode.id);

          // Update the ns parent for all nodes in the new group.
          for (const node of nodes) {
            node.parentId = newGroupNode.id;
          }

          // Update the namespace of all nodes and their desendents in the new
          // group.
          const newNamespacePart = newGroupNodeId;
          const updateNamespace = (node: ModelNode) => {
            const oldNamespace = node.namespace;
            if (oldNamespace === '') {
              node.namespace = newNamespacePart;
            } else {
              if (curGroupNode == null) {
                node.namespace = `${newNamespacePart}/${node.namespace}`;
              } else {
                node.namespace = node.parentId || '';
              }
            }
            node.level = node.namespace.split('/').filter((c) => c !== '').length;
            if (isGroupNode(node)) {
              // Update group node id since its namespace has been changed.
              const oldNodeId = node.id;
              delete modelGraph.nodesById[node.id];
              node.id = `${node.namespace}/${node.id}`;
              modelGraph.nodesById[node.id] = node;

              // Update its parent's children to use the new id.
              if (node.parentId) {
                const nsParent = modelGraph.nodesById[node.parentId] as GroupNode;
                const index = (nsParent.childrenIds || []).indexOf(oldNodeId);
                if (index >= 0) {
                  (nsParent.childrenIds || [])[index] = node.id;
                }
              }

              for (const childId of node.childrenIds || []) {
                const childNode = modelGraph.nodesById[childId];
                if (childNode != null) {
                  // Update its children's nsParent id.
                  childNode.parentId = node.id;
                  // BFS.
                  updateNamespace(childNode);
                }
              }
            }
          };
          for (const node of nodes) {
            updateNamespace(node);
          }

          if (curGroupNode == null) {
            // Remove the nodes in the current new group if they are in the root
            // node list.
            for (const node of nodes) {
              const index = modelGraph.rootNodes.indexOf(node);
              if (index >= 0) {
                modelGraph.rootNodes.splice(index, 1);
              }
            }

            // Add the new group node to root node list if its namespace is
            // empty.
            if (newGroupNode.namespace === '') {
              modelGraph.rootNodes.push(newGroupNode);
            }
          }

          children = newGroupNodes;
        }

        // Update curGrassetNode's childrenIds.
        if (curGroupNode != null) {
          curGroupNode.childrenIds = newGroupNodes.map((node) => node.id);
        }
      }

      for (const child of children) {
        if (isGroupNode(child)) {
          queue.push(child);
        }
      }
    }

    if (hasLargeGroupNodes) {
      this.generateLayoutGraphConnections(modelGraph);
    }
  }

  createEmptyModelGraph(): ModelGraph {
    return {
      id: '<ROOT>',
      nodes: [],
      nodesById: {},
      rootNodes: [],
      edgesByGroupNodeIds: {},
      layoutGraphEdges: {},
    };
  }
}

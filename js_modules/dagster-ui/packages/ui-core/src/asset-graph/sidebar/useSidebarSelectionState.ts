import * as React from 'react';
import {useLayoutEffect} from 'react';

import {GraphData, GraphNode} from '../Utils';

interface SelectedNode {
  id: string;
  path?: string;
}

interface UseSidebarSelectionStateArgs {
  lastSelectedNode: GraphNode | undefined;
  graphData: GraphData;
  sidebarViewType: 'tree' | 'group';
  buildRepoPathForHuman: (repoName: string, locationName: string) => string;
}

/**
 * Hook that manages the selection and expansion state for the asset graph sidebar tree views.
 *
 * Strategy:
 * - Maintains dual tree view states: root-to-leaf (upstream to downstream) and leaf-to-root (downstream to upstream)
 * - Each tree view has its own selection state and set of expanded/open nodes
 * - When a node is selected in the main graph, automatically expands the path to that node in both tree views
 * - Caches node paths to avoid recalculation on every render (stored in lastSelectedSidebarNode* state)
 *
 * State Management:
 * - selectedNode*: Currently selected node in each tree view
 * - openNodes*: Set of node IDs that are expanded/open in each tree view
 * - lastSelectedSidebarNode*: The last selected node for each tree view so that we can scroll to the correct path in the useEffect.
 *
 * Path Building:
 * - For 'tree' view: Builds hierarchical paths by traversing the graph in the specified direction
 * - For 'group' view: Builds location:group paths for organizing assets by repository structure
 * - Uses colon-delimited paths (e.g., "node1:node2:node3") to represent hierarchy
 *
 * Auto-expansion:
 * - When lastSelectedNode changes, automatically expands all nodes along the path from root to the selected node
 * - Ensures the selected node is always visible in both tree views
 *
 * @param args Configuration object containing:
 *   - lastSelectedNode: The currently selected node in the main graph
 *   - graphData: Graph structure with nodes and their upstream/downstream relationships
 *   - sidebarViewType: Either 'tree' (hierarchical) or 'group' (by repository/group)
 *   - buildRepoPathForHuman: Function to format repository paths for display
 *
 * @returns Object containing state and setters for both tree views, plus a collapseAllNodes function
 */
export function useSidebarSelectionState({
  lastSelectedNode,
  graphData,
  sidebarViewType,
  buildRepoPathForHuman,
}: UseSidebarSelectionStateArgs) {
  const [lastSelectedSidebarNodeRootToLeaf, setLastSelectedSidebarNodeRootToLeaf] =
    React.useState<SelectedNode | null>(null);
  const [lastSelectedSidebarNodeLeafToRoot, setLastSelectedSidebarNodeLeafToRoot] =
    React.useState<SelectedNode | null>(null);
  // State for root-to-leaf view
  const [openNodesRootToLeaf, setOpenNodesRootToLeaf] = React.useState<Set<string>>(
    () => new Set(),
  );
  const [selectedNodeRootToLeaf, setSelectedNodeRootToLeaf] = React.useState<SelectedNode | null>(
    null,
  );

  // State for leaf-to-root view
  const [openNodesLeafToRoot, setOpenNodesLeafToRoot] = React.useState<Set<string>>(
    () => new Set(),
  );
  const [selectedNodeLeafToRoot, setSelectedNodeLeafToRoot] = React.useState<SelectedNode | null>(
    null,
  );

  const collapseAllNodes = React.useMemo(() => {
    if (sidebarViewType === 'group') {
      return;
    }
    if (openNodesRootToLeaf.size === 0 && openNodesLeafToRoot.size === 0) {
      return;
    }
    return () => {
      setOpenNodesRootToLeaf(new Set());
      setOpenNodesLeafToRoot(new Set());
    };
  }, [sidebarViewType, openNodesRootToLeaf, openNodesLeafToRoot]);

  useLayoutEffect(() => {
    /**
     * 1. When a node is selected in the main graph, we need to expand all parent nodes
     *    in the sidebar tree views to make the selected node visible.
     *
     * 2. The expansion logic differs based on view type:
     *    - Tree view: Expands the full hierarchical path from root to the selected node
     *    - Group view: Only expands the location and group containing the asset (root-to-leaf only)
     *
     * 3. Both root-to-leaf and leaf-to-root views are updated independently to maintain
     *    their own expansion states.
     */
    if (lastSelectedNode) {
      // Helper function to expand nodes along a path in tree view
      const expandTreePath = (
        prevOpenNodes: Set<string>,
        direction: 'root-to-leaf' | 'leaf-to-root',
        lastSelectedSidebarNode: SelectedNode | null,
        setSelectedNode: (node: SelectedNode) => void,
        selectedNode: SelectedNode | null,
      ) => {
        // Try to reuse cached path if the same node is selected
        let path =
          lastSelectedSidebarNode?.id === lastSelectedNode?.id
            ? lastSelectedSidebarNode.path
            : undefined;

        // Calculate path if not cached
        if (!path) {
          path = getNodePath(lastSelectedNode, direction, graphData);
        }

        const nodesInPath = path.split(':');
        let currentPath = nodesInPath[0];

        if (!currentPath) {
          return prevOpenNodes;
        }

        // Expand all nodes along the path
        const nextOpenNodes = new Set(prevOpenNodes);
        nextOpenNodes.add(currentPath);
        for (let i = 1; i < nodesInPath.length; i++) {
          currentPath = `${currentPath}:${nodesInPath[i]}`;
          nextOpenNodes.add(currentPath);
        }

        // Update selected node if it changed
        if (selectedNode?.id !== lastSelectedNode.id) {
          setSelectedNode({id: lastSelectedNode.id, path: currentPath});
        }

        return nextOpenNodes;
      };

      // Update root-to-leaf view
      setOpenNodesRootToLeaf((prevOpenNodes) => {
        if (sidebarViewType === 'tree') {
          return expandTreePath(
            prevOpenNodes,
            'root-to-leaf',
            lastSelectedSidebarNodeRootToLeaf,
            setSelectedNodeRootToLeaf,
            selectedNodeRootToLeaf,
          );
        }

        // Group view: expand location and group
        const nextOpenNodes = new Set(prevOpenNodes);
        const assetNode = graphData.nodes[lastSelectedNode.id];
        if (assetNode) {
          const locationName = buildRepoPathForHuman(
            assetNode.definition.repository.name,
            assetNode.definition.repository.location.name,
          );
          const groupName = assetNode.definition.groupName || 'default';
          nextOpenNodes.add(locationName);
          nextOpenNodes.add(locationName + ':' + groupName);
        }
        if (selectedNodeRootToLeaf?.id !== lastSelectedNode.id) {
          setSelectedNodeRootToLeaf({id: lastSelectedNode.id});
        }
        return nextOpenNodes;
      });

      // Update leaf-to-root view (only for tree view)
      if (sidebarViewType === 'tree') {
        setOpenNodesLeafToRoot((prevOpenNodes) => {
          return expandTreePath(
            prevOpenNodes,
            'leaf-to-root',
            lastSelectedSidebarNodeLeafToRoot,
            setSelectedNodeLeafToRoot,
            selectedNodeLeafToRoot,
          );
        });
      }
    } else {
      // Clear selection when no node is selected
      setSelectedNodeRootToLeaf(null);
      setSelectedNodeLeafToRoot(null);
    }
  }, [
    lastSelectedNode,
    lastSelectedSidebarNodeRootToLeaf,
    lastSelectedSidebarNodeLeafToRoot,
    graphData,
    sidebarViewType,
    buildRepoPathForHuman,
    selectedNodeRootToLeaf,
    selectedNodeLeafToRoot,
  ]);

  return {
    selectedNodeRootToLeaf,
    setSelectedNodeRootToLeaf,
    selectedNodeLeafToRoot,
    setSelectedNodeLeafToRoot,
    openNodesRootToLeaf,
    setOpenNodesRootToLeaf,
    openNodesLeafToRoot,
    setOpenNodesLeafToRoot,
    collapseAllNodes,
    setLastSelectedSidebarNodeRootToLeaf,
    setLastSelectedSidebarNodeLeafToRoot,
  };
}

/**
 * Builds a colon-delimited path from the root (or leaf) to the given node by traversing
 * the graph in the specified direction.
 *
 * Algorithm:
 * - Starts from the given node and traverses upstream (for root-to-leaf) or downstream (for leaf-to-root)
 * - Builds path by prepending each ancestor node ID
 * - Uses a 'seen' set to prevent infinite loops in cyclic graphs
 * - Continues until no more adjacent nodes are found
 *
 * @param node The target node to build a path to
 * @param direction Whether to traverse upstream (root-to-leaf) or downstream (leaf-to-root)
 * @param graphData Graph structure containing node relationships
 * @returns Colon-delimited path string (e.g., "root:parent:node")
 */
function getNodePath(
  node: GraphNode,
  direction: 'root-to-leaf' | 'leaf-to-root',
  graphData: GraphData,
) {
  let path = node.id;
  let currentId = node.id;
  let next: string[];
  const seen = new Set<string>();
  while ((next = getAdjacentNodes(graphData, currentId, direction))) {
    const candidates = next;
    if (!candidates.length) {
      break;
    }
    while (true) {
      const next = candidates.shift();
      if (!next) {
        break;
      }
      if (graphData.nodes[next] && !seen.has(next)) {
        seen.add(next);
        path = `${next}:${path}`;
        currentId = next;
      } else {
        break;
      }
    }
  }
  return path;
}

/**
 * Retrieves adjacent nodes based on the traversal direction.
 *
 * @param graphData Graph structure with upstream/downstream relationships
 * @param id Node ID to get adjacent nodes for
 * @param direction Determines which edges to follow:
 *   - 'root-to-leaf': Returns upstream nodes (dependencies)
 *   - 'leaf-to-root': Returns downstream nodes (dependents)
 * @returns Array of adjacent node IDs
 */
function getAdjacentNodes(
  graphData: GraphData,
  id: string,
  direction: 'root-to-leaf' | 'leaf-to-root',
) {
  if (direction === 'root-to-leaf') {
    return Object.keys(graphData.upstream[id] ?? {});
  }
  return Object.keys(graphData.downstream[id] ?? {});
}

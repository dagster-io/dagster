import * as React from 'react';

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

  React.useLayoutEffect(() => {
    if (lastSelectedNode) {
      // Update root-to-leaf view
      setOpenNodesRootToLeaf((prevOpenNodes) => {
        if (sidebarViewType === 'tree') {
          let path;
          if (lastSelectedSidebarNodeRootToLeaf?.id === lastSelectedNode?.id) {
            path = lastSelectedSidebarNodeRootToLeaf.path;
          }
          if (!path) {
            path = getNodePath(lastSelectedNode, 'root-to-leaf', graphData);
          }

          const nodesInPath = path.split(':');
          let currentPath = nodesInPath[0];

          if (!currentPath) {
            return prevOpenNodes;
          }

          const nextOpenNodes = new Set(prevOpenNodes);
          nextOpenNodes.add(currentPath);
          for (let i = 1; i < nodesInPath.length; i++) {
            currentPath = `${currentPath}:${nodesInPath[i]}`;
            nextOpenNodes.add(currentPath);
          }
          if (selectedNodeRootToLeaf?.id !== lastSelectedNode.id) {
            setSelectedNodeRootToLeaf({id: lastSelectedNode.id, path: currentPath});
          }
          return nextOpenNodes;
        }
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

      // Update leaf-to-root view
      setOpenNodesLeafToRoot((prevOpenNodes) => {
        let path;
        if (lastSelectedSidebarNodeLeafToRoot?.id === lastSelectedNode?.id) {
          path = lastSelectedSidebarNodeLeafToRoot.path;
        }
        if (!path) {
          path = getNodePath(lastSelectedNode, 'leaf-to-root', graphData);
        }

        const nodesInPath = path.split(':');
        let currentPath = nodesInPath[0];

        if (!currentPath) {
          return prevOpenNodes;
        }

        const nextOpenNodes = new Set(prevOpenNodes);
        nextOpenNodes.add(currentPath);
        for (let i = 1; i < nodesInPath.length; i++) {
          currentPath = `${currentPath}:${nodesInPath[i]}`;
          nextOpenNodes.add(currentPath);
        }
        if (selectedNodeLeafToRoot?.id !== lastSelectedNode.id) {
          setSelectedNodeLeafToRoot({id: lastSelectedNode.id, path: currentPath});
        }
        return nextOpenNodes;
      });
    } else {
      setSelectedNodeRootToLeaf(null);
      setSelectedNodeLeafToRoot(null);
    }
  }, [
    lastSelectedNode,
    lastSelectedSidebarNodeRootToLeaf,
    lastSelectedSidebarNodeLeafToRoot,
    graphData,
    sidebarViewType,
    selectedNodeRootToLeaf?.id,
    selectedNodeLeafToRoot?.id,
    buildRepoPathForHuman,
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

function getNodePath(
  node: GraphNode,
  direction: 'root-to-leaf' | 'leaf-to-root',
  graphData: GraphData,
) {
  let path = node.id;
  let currentId = node.id;
  let next: string[];
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
      if (graphData.nodes[next]) {
        path = `${next}:${path}`;
        currentId = next;
      } else {
        break;
      }
    }
  }
  return path;
}

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

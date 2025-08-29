import {FolderNodeType, TreeNodeType} from './util';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {GraphData, GraphNode, groupIdForNode, tokenForAssetKey} from '../Utils';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export function getRootNodes(graphData: GraphData): string[] {
  return Object.keys(graphData.nodes)
    .filter(
      (id) =>
        // When we filter to a subgraph, the nodes at the root aren't real roots, but since
        // their upstream graph is cutoff we want to show them as roots in the sidebar.
        // Find these nodes by filtering on whether there parent nodes are in assetGraphData
        !Object.keys(graphData.upstream[id] ?? {}).filter((id) => graphData.nodes[id]).length,
    )
    .sort((a, b) =>
      COLLATOR.compare(getDisplayName(graphData.nodes[a]), getDisplayName(graphData.nodes[b])),
    );
}

export function getLeafNodes(graphData: GraphData): string[] {
  return Object.keys(graphData.nodes)
    .filter(
      (id) =>
        // Leaf nodes are those with no downstream dependencies
        !Object.keys(graphData.downstream[id] ?? {}).filter((id) => graphData.nodes[id]).length,
    )
    .sort((a, b) =>
      COLLATOR.compare(
        graphData.nodes[a] ? getDisplayName(graphData.nodes[a]) : '',
        graphData.nodes[b] ? getDisplayName(graphData.nodes[b]) : '',
      ),
    );
}

export function buildTreeNodesRootToLeaf(
  graphData: GraphData,
  rootNodes: string[],
  openNodesRootToLeaf: Set<string>,
): TreeNodeType[] {
  const queue = rootNodes.map((id) => ({level: 1, id, path: id}));
  const treeNodes: TreeNodeType[] = [];

  while (true) {
    const node = queue.shift();
    if (!node) {
      break;
    }
    treeNodes.push(node);
    if (openNodesRootToLeaf.has(node.path)) {
      const downstream = Object.keys(graphData.downstream[node.id] || {}).filter(
        (id) => graphData.nodes[id],
      );
      queue.unshift(
        ...downstream.map((id) => ({level: node.level + 1, id, path: `${node.path}:${id}`})),
      );
    }
  }
  return treeNodes;
}

export function buildTreeNodesLeafToRoot(
  graphData: GraphData,
  leafNodes: string[],
  openNodesLeafToRoot: Set<string>,
): TreeNodeType[] {
  const queue = leafNodes.map((id) => ({level: 1, id, path: id}));
  const treeNodes: TreeNodeType[] = [];

  while (true) {
    const node = queue.shift();
    if (!node) {
      break;
    }
    treeNodes.push(node);
    if (openNodesLeafToRoot.has(node.path)) {
      const upstream = Object.keys(graphData.upstream[node.id] || {}).filter(
        (id) => graphData.nodes[id],
      );
      queue.unshift(
        ...upstream.map((id) => ({level: node.level + 1, id, path: `${node.path}:${id}`})),
      );
    }
  }
  return treeNodes;
}

export function buildFolderNodes(
  graphData: GraphData,
  openNodesRootToLeaf: Set<string>,
): FolderNodeType[] {
  const folderNodes: FolderNodeType[] = [];

  // Map of Code Locations -> Groups -> Assets
  const codeLocationNodes: Record<
    string,
    {
      locationName: string;
      groups: Record<
        string,
        {
          groupName: string;
          assets: GraphNode[];
          repositoryName: string;
          repositoryLocationName: string;
        }
      >;
    }
  > = {};

  let groupsCount = 0;
  Object.values(graphData.nodes).forEach((node) => {
    const locationName = node.definition.repository.location.name;
    const repositoryName = node.definition.repository.name;
    const groupName = node.definition.groupName || 'default';
    const groupId = groupIdForNode(node);
    const codeLocation = buildRepoPathForHuman(repositoryName, locationName);
    codeLocationNodes[codeLocation] = codeLocationNodes[codeLocation] || {
      locationName: codeLocation,
      groups: {},
    };
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    if (!codeLocationNodes[codeLocation]!.groups[groupId]!) {
      groupsCount += 1;
    }
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    codeLocationNodes[codeLocation]!.groups[groupId] = codeLocationNodes[codeLocation]!.groups[
      groupId
    ] || {
      groupName,
      assets: [],
      repositoryName,
      repositoryLocationName: locationName,
    };
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    codeLocationNodes[codeLocation]!.groups[groupId]!.assets.push(node);
  });

  const codeLocationsCount = Object.keys(codeLocationNodes).length;
  Object.entries(codeLocationNodes)
    .sort(([_1, a], [_2, b]) => COLLATOR.compare(a.locationName, b.locationName))
    .forEach(([locationName, locationNode]) => {
      folderNodes.push({
        locationName,
        id: locationName,
        level: 1,
        openAlways: codeLocationsCount === 1,
      });
      if (openNodesRootToLeaf.has(locationName) || codeLocationsCount === 1) {
        Object.entries(locationNode.groups)
          .sort(([_1, a], [_2, b]) => COLLATOR.compare(a.groupName, b.groupName))
          .forEach(([id, groupNode]) => {
            folderNodes.push({
              groupNode,
              id,
              level: 2,
            });
            if (openNodesRootToLeaf.has(id) || groupsCount === 1) {
              groupNode.assets
                .sort((a, b) => COLLATOR.compare(a.id, b.id))
                .forEach((assetNode) => {
                  folderNodes.push({
                    id: assetNode.id,
                    path: [
                      locationName,
                      groupNode.groupName,
                      tokenForAssetKey(assetNode.assetKey),
                    ].join(':'),
                    level: 3,
                  });
                });
            }
          });
      }
    });

  if (groupsCount === 1) {
    return folderNodes
      .filter((node) => node.level === 3)
      .map((node) => ({
        ...node,
        level: 1,
      }));
  }

  return folderNodes;
}

function getDisplayName(node?: GraphNode) {
  return node?.assetKey.path[node?.assetKey.path.length - 1] ?? '';
}

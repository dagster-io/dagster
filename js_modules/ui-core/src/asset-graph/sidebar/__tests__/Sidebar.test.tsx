import {buildAssetKey, buildAssetNode} from '../../../graphql/builders';
import {GraphData, ancestorGroupIds, buildGraphData, groupIdForNode} from '../../Utils';
import {buildRenderedNodes} from '../Sidebar';

function graphDataFor(assets: {path: string[]; groupName: string}[]): GraphData {
  return buildGraphData(
    assets.map(({path, groupName}) =>
      buildAssetNode({
        id: JSON.stringify(path),
        assetKey: buildAssetKey({path}),
        groupName,
        dependencyKeys: [],
        dependedByKeys: [],
      }),
    ),
  );
}

// Every group in the fixture, open, so the assets inside them are emitted.
// Ancestors count too — flattenGroupTree won't descend past a closed parent.
function allGroupsOpen(graphData: GraphData) {
  const open = new Set<string>();
  for (const node of Object.values(graphData.nodes)) {
    const leafId = groupIdForNode(node);
    open.add(leafId);
    ancestorGroupIds(leafId).forEach((id) => open.add(id));
  }
  return open;
}

function labelsOf(graphData: GraphData, rows: ReturnType<typeof buildRenderedNodes>) {
  return rows.map((row) => {
    if ('groupNode' in row) {
      return `group:${row.groupNode.groupName}`;
    }
    const node = graphData.nodes[row.id];
    // The sidebar renders the leaf segment of the asset key as the row's label.
    return node ? node.assetKey.path[node.assetKey.path.length - 1] : row.id;
  });
}

describe('buildRenderedNodes', () => {
  it('sorts assets within a group by their displayed label, not their full key', () => {
    // `zzz/apple` renders as "apple" and `aaa/banana` renders as "banana", so
    // ordering on the full key would put banana first even though the sidebar
    // shows apple, banana.
    const graphData = graphDataFor([
      {path: ['zzz', 'apple'], groupName: 'produce'},
      {path: ['aaa', 'banana'], groupName: 'produce'},
      {path: ['mmm', 'cherry'], groupName: 'produce'},
    ]);

    // A single group with no hierarchy renders assets at the root.
    expect(labelsOf(graphData, buildRenderedNodes(graphData.nodes, new Set()))).toEqual([
      'apple',
      'banana',
      'cherry',
    ]);
  });

  it('sorts groups alphabetically by name', () => {
    const graphData = graphDataFor([
      {path: ['one'], groupName: 'zebra'},
      {path: ['two'], groupName: 'aardvark'},
      {path: ['three'], groupName: 'manatee'},
    ]);

    expect(labelsOf(graphData, buildRenderedNodes(graphData.nodes, new Set()))).toEqual([
      'group:aardvark',
      'group:manatee',
      'group:zebra',
    ]);
  });

  it('sorts assets alphabetically inside each group', () => {
    const graphData = graphDataFor([
      {path: ['delta'], groupName: 'zebra'},
      {path: ['charlie'], groupName: 'zebra'},
      {path: ['bravo'], groupName: 'aardvark'},
      {path: ['alpha'], groupName: 'aardvark'},
    ]);

    expect(
      labelsOf(graphData, buildRenderedNodes(graphData.nodes, allGroupsOpen(graphData))),
    ).toEqual(['group:aardvark', 'alpha', 'bravo', 'group:zebra', 'charlie', 'delta']);
  });

  it('is independent of the order assets arrive in the graph', () => {
    const forward = graphDataFor([
      {path: ['alpha'], groupName: 'aardvark'},
      {path: ['bravo'], groupName: 'aardvark'},
      {path: ['charlie'], groupName: 'zebra'},
    ]);
    const reversed = graphDataFor([
      {path: ['charlie'], groupName: 'zebra'},
      {path: ['bravo'], groupName: 'aardvark'},
      {path: ['alpha'], groupName: 'aardvark'},
    ]);

    expect(labelsOf(forward, buildRenderedNodes(forward.nodes, allGroupsOpen(forward)))).toEqual(
      labelsOf(reversed, buildRenderedNodes(reversed.nodes, allGroupsOpen(reversed))),
    );
  });

  it('sorts nested group segments alphabetically at each level', () => {
    const graphData = graphDataFor([
      {path: ['one'], groupName: 'marketing/sales'},
      {path: ['two'], groupName: 'marketing/ads'},
      {path: ['three'], groupName: 'finance'},
    ]);

    expect(
      labelsOf(graphData, buildRenderedNodes(graphData.nodes, allGroupsOpen(graphData))),
    ).toEqual([
      'group:finance',
      'three',
      'group:marketing',
      'group:marketing/ads',
      'two',
      'group:marketing/sales',
      'one',
    ]);
  });
});

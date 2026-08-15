import {buildAssetKey, buildAssetNode} from '../../../graphql/builders';
import {GraphData, buildGraphData} from '../../Utils';
import {buildSidebarSearchValues} from '../searchValues';

function graphDataFor(paths: string[][]): GraphData {
  return buildGraphData(
    paths.map((path) =>
      buildAssetNode({
        id: JSON.stringify(path),
        assetKey: buildAssetKey({path}),
        dependencyKeys: [],
        dependedByKeys: [],
      }),
    ),
  );
}

describe('buildSidebarSearchValues', () => {
  it('offers exactly the assets in the graph it was given', () => {
    const graphData = graphDataFor([['alpha'], ['bravo']]);

    expect(buildSidebarSearchValues(graphData.nodes).map((v) => v.label)).toEqual([
      'alpha',
      'bravo',
    ]);
  });

  it('returns nothing for an empty graph', () => {
    expect(buildSidebarSearchValues({})).toEqual([]);
  });

  it('labels each entry with the leaf segment and keeps the full key as path', () => {
    const graphData = graphDataFor([['raw', 'orders']]);

    expect(buildSidebarSearchValues(graphData.nodes)).toEqual([
      {
        value: JSON.stringify(['raw', 'orders']),
        label: 'orders',
        path: 'raw/orders',
        namespace: 'raw',
      },
    ]);
  });

  it('leaves the namespace empty for a single-segment key', () => {
    const graphData = graphDataFor([['orders']]);

    expect(buildSidebarSearchValues(graphData.nodes)[0]).toMatchObject({
      label: 'orders',
      path: 'orders',
      namespace: '',
    });
  });

  it('joins all but the leaf segment into the namespace', () => {
    const graphData = graphDataFor([['analytics', 'warehouse', 'marts', 'daily_revenue']]);

    expect(buildSidebarSearchValues(graphData.nodes)[0]).toMatchObject({
      label: 'daily_revenue',
      namespace: 'analytics/warehouse/marts',
    });
  });

  it('uses the graph id as the value so selectNode can resolve it', () => {
    const graphData = graphDataFor([['raw', 'orders']]);
    const [entry] = buildSidebarSearchValues(graphData.nodes);

    // The sidebar looks the selection up as graphData.nodes[value].
    expect(entry && graphData.nodes[entry.value]).toBeDefined();
  });

  it('sorts by the displayed label rather than the full key', () => {
    const graphData = graphDataFor([
      ['zzz', 'apple'],
      ['aaa', 'banana'],
      ['mmm', 'cherry'],
    ]);

    expect(buildSidebarSearchValues(graphData.nodes).map((v) => v.label)).toEqual([
      'apple',
      'banana',
      'cherry',
    ]);
  });

  it('orders entries that share a label by their full key', () => {
    const graphData = graphDataFor([
      ['staging', 'orders'],
      ['raw', 'orders'],
    ]);

    expect(buildSidebarSearchValues(graphData.nodes).map((v) => v.path)).toEqual([
      'raw/orders',
      'staging/orders',
    ]);
  });

  it('is independent of the order assets arrive in the graph', () => {
    const forward = graphDataFor([['alpha'], ['bravo'], ['charlie']]);
    const reversed = graphDataFor([['charlie'], ['bravo'], ['alpha']]);

    expect(buildSidebarSearchValues(forward.nodes)).toEqual(
      buildSidebarSearchValues(reversed.nodes),
    );
  });
});

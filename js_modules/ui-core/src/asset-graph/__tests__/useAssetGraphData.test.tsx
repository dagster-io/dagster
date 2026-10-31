import {renderHook} from '@testing-library/react';
import cloneDeep from 'lodash/cloneDeep';

import {GraphQueryItem} from '../../app/GraphQueryImpl';
import {WorkspaceAssetNode} from '../../assets/useAllAssets';
import {buildAssetKey, buildAssetNode} from '../../graphql/builders';
import {calculateGraphDistances, useAssetGraphData} from '../useAssetGraphData';

const mockAssets = [
  {definition: buildAssetNode({assetKey: buildAssetKey({path: ['a']}), dependencyKeys: []})},
];
let mockShowAssetsWithoutDefinitions = false;

jest.mock('../../assets/useAllAssets', () => ({
  useAllAssetsNodes: () => ({assets: mockAssets, loading: false}),
}));

jest.mock('../../app/UserSettingsDialog/useShowAssetsWithoutDefinitions', () => ({
  useShowAssetsWithoutDefinitions: () => ({
    showAssetsWithoutDefinitions: mockShowAssetsWithoutDefinitions,
  }),
}));

jest.mock('../../app/UserSettingsDialog/useShowStubAssets', () => ({
  useShowStubAssets: () => ({showStubAssets: false}),
}));

const mockSupplementaryData = {loading: false, data: {}};
jest.mock('@shared/asset-graph/useAssetGraphSupplementaryData', () => ({
  useAssetGraphSupplementaryData: () => mockSupplementaryData,
}));

const TEST_GRAPH: GraphQueryItem[] = [
  // Top Layer
  {
    name: 'A',
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}, {solid: {name: 'H'}}]}],
  },
  {
    name: 'B',
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'D'}}, {solid: {name: 'C'}}]}],
  },

  // Second Layer
  {
    name: 'C',
    inputs: [{dependsOn: [{solid: {name: 'A'}}, {solid: {name: 'B'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'E'}}]}],
  },
  {
    name: 'D',
    inputs: [{dependsOn: [{solid: {name: 'B'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'E'}}, {solid: {name: 'H'}}]}],
  },

  // Third Layer
  {
    name: 'E',
    inputs: [{dependsOn: [{solid: {name: 'C'}}, {solid: {name: 'D'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'F'}}, {solid: {name: 'G'}}]}],
  },

  // Fourth Layer
  {
    name: 'F',
    inputs: [{dependsOn: [{solid: {name: 'E'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'H'}}]}],
  },
  {
    name: 'G',
    inputs: [{dependsOn: [{solid: {name: 'E'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'H'}}]}],
  },

  // Fifth Layer with some deps that skip layers
  {
    name: 'H',
    inputs: [
      {
        dependsOn: [
          {solid: {name: 'F'}},
          {solid: {name: 'G'}},
          {solid: {name: 'A'}},
          {solid: {name: 'D'}},
        ],
      },
    ],
    outputs: [],
  },
];

describe('calculateGraphDistances', () => {
  it('traverses correctly', () => {
    const fromA = calculateGraphDistances(TEST_GRAPH, {path: ['A']});
    expect(fromA.upstream).toEqual(0);
    expect(fromA.downstream).toEqual(3);
    const fromD = calculateGraphDistances(TEST_GRAPH, {path: ['D']});
    expect(fromD.upstream).toEqual(1);
    expect(fromD.downstream).toEqual(2);
    const fromH = calculateGraphDistances(TEST_GRAPH, {path: ['H']});
    expect(fromH.upstream).toEqual(3);
    expect(fromH.downstream).toEqual(0);
  });

  it('traverses correctly if items contains disconnected graphs', () => {
    const TWO_GRAPHS = cloneDeep(TEST_GRAPH);

    // Break the test graph in two at E
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    TWO_GRAPHS.find((item) => item.name === 'E')!.outputs = [];
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    TWO_GRAPHS.find((item) => item.name === 'D')!.outputs = [];
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    TWO_GRAPHS.find((item) => item.name === 'F')!.inputs = [];
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    TWO_GRAPHS.find((item) => item.name === 'G')!.inputs = [];
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    TWO_GRAPHS.find((item) => item.name === 'H')!.inputs = [
      {dependsOn: [{solid: {name: 'F'}}, {solid: {name: 'G'}}]},
    ];

    const fromA = calculateGraphDistances(TWO_GRAPHS, {path: ['A']});
    expect(fromA.upstream).toEqual(0);
    expect(fromA.downstream).toEqual(2);
    const fromD = calculateGraphDistances(TWO_GRAPHS, {path: ['D']});
    expect(fromD.upstream).toEqual(1);
    expect(fromD.downstream).toEqual(0);
    const fromH = calculateGraphDistances(TWO_GRAPHS, {path: ['H']});
    expect(fromH.upstream).toEqual(1);
    expect(fromH.downstream).toEqual(0);
  });

  it('returns zero if data is not present', () => {
    expect(calculateGraphDistances([], {path: ['asset']}).upstream).toEqual(0);
    expect(calculateGraphDistances([], {path: ['asset']}).downstream).toEqual(0);
  });

  it('returns zero if the asset is not found in the graph', () => {
    expect(calculateGraphDistances(TEST_GRAPH, {path: ['asset']}).upstream).toEqual(0);
    expect(calculateGraphDistances(TEST_GRAPH, {path: ['asset']}).downstream).toEqual(0);
  });
});

describe('useAssetGraphData', () => {
  const externalAssets = [{id: 'external', key: {path: ['external']}}];
  const hideNodesMatching = (_node: WorkspaceAssetNode) => false;

  it.each([
    {name: 'without definitions hidden', showAssetsWithoutDefinitions: false, externalAssets},
    {name: 'without definitions shown', showAssetsWithoutDefinitions: true, externalAssets},
    {name: 'no external assets', showAssetsWithoutDefinitions: true, externalAssets: undefined},
  ])(
    'shares graph query items across instances with the same inputs ($name)',
    ({showAssetsWithoutDefinitions, externalAssets}) => {
      mockShowAssetsWithoutDefinitions = showAssetsWithoutDefinitions;
      const {result} = renderHook(() => [
        useAssetGraphData('*', {hideNodesMatching, externalAssets}),
        useAssetGraphData('*', {hideNodesMatching, externalAssets}),
      ]);
      const [first, second] = result.current;
      expect(second?.graphQueryItems).toBe(first?.graphQueryItems);
    },
  );
});

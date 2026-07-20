import assert from 'node:assert/strict';
import os from 'node:os';
import {performance} from 'node:perf_hooks';

import {
  applyAssetGroupLineageRouting,
  type ApplyAssetGroupRoutingOptions,
  type RoutingLayout,
} from '../assetGroupLineageRouting';

const GROUP_COUNT = 9_999;
const EDGE_COUNT = 17_999;
const WARMUP_COUNT = 3;
const SAMPLE_COUNT = 7;
const MAX_MEDIAN_MS = 50;
const MAX_MEDIAN_HEAP_MB = 10;
const CANONICAL_COMMAND = 'yarn benchmark:asset-group-lineage-routing';

if (!global.gc) {
  throw new Error(`Benchmark requires exposed garbage collection. Run: ${CANONICAL_COMMAND}`);
}
const forceGc = global.gc;

const groupId = (index: number) => `group-${index.toString().padStart(4, '0')}`;
const nodeId = (index: number) => `node-${index.toString().padStart(4, '0')}`;

const createNormalFixture = (): {
  layout: RoutingLayout;
  options: ApplyAssetGroupRoutingOptions;
} => {
  const groups: RoutingLayout['groups'] = {};
  const nodes: RoutingLayout['nodes'] = {};
  const groupParentById: ApplyAssetGroupRoutingOptions['groupParentById'] = {};
  const ownerGroupByNodeId: ApplyAssetGroupRoutingOptions['ownerGroupByNodeId'] = {};
  const endpointGroupById: ApplyAssetGroupRoutingOptions['endpointGroupById'] = {};

  for (let index = 0; index < GROUP_COUNT; index++) {
    const currentGroupId = groupId(index);
    const currentNodeId = nodeId(index);
    const x = index * 10;
    groups[currentGroupId] = {
      id: currentGroupId,
      bounds: {x, y: 0, width: 5, height: 10},
      expanded: true,
    };
    nodes[currentNodeId] = {
      id: currentNodeId,
      bounds: {x: x + 1, y: 1, width: 3, height: 8},
    };
    groupParentById[currentGroupId] = null;
    ownerGroupByNodeId[currentNodeId] = currentGroupId;
    endpointGroupById[currentNodeId] = currentGroupId;
  }

  const edges: RoutingLayout['edges'] = [];
  const addEdge = (sourceIndex: number, targetIndex: number) => {
    edges.push({
      fromId: nodeId(sourceIndex),
      toId: nodeId(targetIndex),
      from: {x: sourceIndex * 10 + 4, y: 5},
      to: {x: targetIndex * 10 + 1, y: 5},
    });
  };
  for (let index = 0; index < GROUP_COUNT - 1; index++) {
    addEdge(index, index + 1);
  }
  for (let index = 0; edges.length < EDGE_COUNT; index++) {
    addEdge(index, index + 2);
  }

  assert.equal(Object.keys(groups).length, GROUP_COUNT);
  assert.equal(Object.keys(nodes).length, GROUP_COUNT);
  assert.equal(edges.length, EDGE_COUNT);

  return {
    layout: {width: GROUP_COUNT * 10, height: 10, groups, nodes, edges},
    options: {
      direction: 'horizontal',
      ranksep: 60,
      trailingGroupPadding: 15,
      margin: 100,
      groupParentById,
      ownerGroupByNodeId,
      endpointGroupById,
    },
  };
};

const createDeepFixture = (): {
  layout: RoutingLayout;
  options: ApplyAssetGroupRoutingOptions;
} => {
  const groups: RoutingLayout['groups'] = {};
  const groupParentById: ApplyAssetGroupRoutingOptions['groupParentById'] = {};
  for (let depth = 0; depth < 300; depth++) {
    const id = `nested-${depth}`;
    groups[id] = {
      id,
      bounds: {x: depth, y: depth, width: 500 - depth, height: 500 - depth},
      expanded: true,
    };
    groupParentById[id] = depth === 0 ? null : `nested-${depth - 1}`;
  }
  groups.target = {
    id: 'target',
    bounds: {x: 1000, y: 0, width: 5, height: 10},
    expanded: true,
  };
  groupParentById.target = null;

  const nodes: RoutingLayout['nodes'] = {
    source: {id: 'source', bounds: {x: 300, y: 300, width: 5, height: 5}},
    target: {id: 'target', bounds: {x: 1001, y: 1, width: 3, height: 8}},
  };
  return {
    layout: {
      width: 1100,
      height: 500,
      groups,
      nodes,
      edges: [{fromId: 'source', toId: 'target', from: {x: 305, y: 302}, to: {x: 1001, y: 5}}],
    },
    options: {
      direction: 'horizontal',
      ranksep: 60,
      trailingGroupPadding: 15,
      margin: 100,
      groupParentById,
      ownerGroupByNodeId: {source: 'nested-299', target: 'target'},
      endpointGroupById: {source: 'nested-299', target: 'target'},
    },
  };
};

const median = (values: number[]) => {
  assert.ok(
    values.length > 0 && values.length % 2 === 1,
    'Median requires a positive odd sample count',
  );
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)]!;
};

const normal = createNormalFixture();
for (let index = 0; index < WARMUP_COUNT; index++) {
  const result = applyAssetGroupLineageRouting(normal.layout, normal.options);
  assert.equal(result.edges.length, EDGE_COUNT);
}

const elapsedSamples: number[] = [];
const rawHeapSamples: number[] = [];
const retainedHeapSamples: number[] = [];
const retainedResults: RoutingLayout[] = [];
for (let index = 0; index < SAMPLE_COUNT; index++) {
  retainedResults.length = 0;
  forceGc();
  const heapBefore = process.memoryUsage().heapUsed;
  const startedAt = performance.now();
  const result = applyAssetGroupLineageRouting(normal.layout, normal.options);
  const elapsed = performance.now() - startedAt;
  const rawHeapDelta = process.memoryUsage().heapUsed - heapBefore;
  retainedResults.push(result);
  forceGc();
  const retainedHeapDelta = process.memoryUsage().heapUsed - heapBefore;
  const retainedResult = retainedResults[0];
  assert.equal(retainedResult, result);
  assert.notEqual(result, normal.layout);
  assert.equal(retainedResult.edges.length, EDGE_COUNT);
  assert.equal(Object.keys(retainedResult.groups).length, GROUP_COUNT);
  assert.equal(Object.keys(retainedResult.nodes).length, GROUP_COUNT);
  elapsedSamples.push(elapsed);
  rawHeapSamples.push(rawHeapDelta / (1024 * 1024));
  retainedHeapSamples.push(retainedHeapDelta / (1024 * 1024));
}

const measuredResult = retainedResults[0]!;
const firstEdge = measuredResult.edges[0]!;
assert.deepEqual(firstEdge, {
  fromId: nodeId(0),
  toId: nodeId(1),
  from: {x: 4, y: 5},
  to: {x: 66, y: 5},
  sourceBoundary: 5,
  targetBoundary: 65,
});
const lastEdge = measuredResult.edges[EDGE_COUNT - 1]!;
assert.deepEqual(lastEdge, {
  fromId: nodeId(8000),
  toId: nodeId(8002),
  from: {x: 520_004, y: 5},
  to: {x: 520_131, y: 5},
  sourceBoundary: 520_005,
  targetBoundary: 520_130,
});
for (const edge of [firstEdge, lastEdge]) {
  assert.ok(edge.sourceBoundary !== undefined && edge.targetBoundary !== undefined);
  assert.ok(edge.from.x <= edge.sourceBoundary);
  assert.ok(edge.sourceBoundary + 60 <= edge.targetBoundary);
  assert.ok(edge.targetBoundary <= edge.to.x);
}

const deep = createDeepFixture();
const depthStartedAt = performance.now();
const deepResult = applyAssetGroupLineageRouting(deep.layout, deep.options);
const depth300Ms = performance.now() - depthStartedAt;
assert.notEqual(deepResult, deep.layout);
assert.equal(deepResult.edges.length, 1);

const medianMs = median(elapsedSamples);
const medianRawHeapMb = median(rawHeapSamples);
const medianRetainedHeapMb = median(retainedHeapSamples);
const output = {
  node: process.version,
  cpu: os.cpus()[0]?.model ?? 'unknown',
  groups: GROUP_COUNT,
  edges: EDGE_COUNT,
  medianMs,
  medianHeapMb: medianRetainedHeapMb,
  medianRawHeapMb,
  medianRetainedHeapMb,
  depth300Ms,
};
console.log(output);

assert.ok(medianMs <= MAX_MEDIAN_MS, `Median ${medianMs.toFixed(2)}ms exceeds ${MAX_MEDIAN_MS}ms`);
assert.ok(
  medianRetainedHeapMb <= MAX_MEDIAN_HEAP_MB,
  `Median retained heap delta ${medianRetainedHeapMb.toFixed(2)}MB exceeds ${MAX_MEDIAN_HEAP_MB}MB`,
);

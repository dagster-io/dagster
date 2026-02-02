import memoize from 'lodash/memoize';
import {useEffect, useLayoutEffect, useMemo, useReducer, useRef} from 'react';
import {Worker} from 'shared/workers/Worker.oss';

import {ILayoutOp, LayoutOpGraphOptions, OpGraphLayout, layoutOpGraph} from './layout';
import {asyncMemoize, indexedDBAsyncMemoize} from '../app/Util';
import {PreflightCheckResult, runPreflightChecks} from '../asset-graph/PreflightChecks';
import {GraphData, buildGraphDataFromOps} from '../asset-graph/Utils';
import {AssetGraphLayout, LayoutAssetGraphOptions, layoutAssetGraph} from '../asset-graph/layout';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {hashObject} from '../util/hashObject';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {workerSpawner} from '../workers/workerSpawner';

/**
 * Determines if an asset graph is too large to render without an explicit query.
 * Returns true if the graph exceeds node, edge, or path length thresholds.
 */
export function renderingModeForGraph(
  analysis: PreflightCheckResult,
  forceLargeGraph?: boolean,
): {error: 'cycles' | 'too-large' | null; async: boolean} {
  if (analysis.hasCycles) {
    return {error: 'cycles', async: false};
  }

  if (!forceLargeGraph) {
    if (analysis.nodeCount >= 10_000) {
      console.warn(`Graph contains ${analysis.nodeCount} nodes, more than 10,000 suggested limit.`);
      return {error: 'too-large', async: false};
    }
    if (analysis.edgeCount >= 18_000) {
      console.warn(`Graph contains ${analysis.edgeCount} edges, more than 18,000 suggested limit.`);
      return {error: 'too-large', async: false};
    }
    if (analysis.longestPath >= 300) {
      console.warn(`Graph has depth ${analysis.longestPath}, more than 300 suggested limit.`);
      return {error: 'too-large', async: false};
    }
  }

  return {error: null, async: analysis.nodeCount >= 50};
}

// If you're working on the layout logic, set to false so hot-reloading re-computes the layout
const CACHING_ENABLED = true;

// Op Graph

const _opLayoutCacheKey = (ops: ILayoutOp[], opts: LayoutOpGraphOptions) => {
  const solidKey = ops.map((x) => x.name).join('|');
  const parentKey = opts.parentOp?.name;
  return `${solidKey}:${parentKey}`;
};

export const getFullOpLayout = memoize(layoutOpGraph, _opLayoutCacheKey);

const asyncGetFullOpLayout = asyncMemoize((ops: ILayoutOp[], opts: LayoutOpGraphOptions) => {
  return new Promise<OpGraphLayout>((resolve) => {
    const worker = spawnLayoutWorker();
    worker.onMessage((event) => {
      resolve(event.data);
      worker.terminate();
    });
    worker.postMessage({type: 'layoutOpGraph', ops, opts});
  });
}, _opLayoutCacheKey);

const _assetLayoutCacheKey = weakMapMemoize(
  (graphData: GraphData, opts: LayoutAssetGraphOptions) => {
    // IMPORTANT: hashObject internally uses weakmapMemoize to avoid re-calculating
    // the hash for the same object twice. Hashing individual objects and joining the
    // strings allows this Weakmap to re-use `graphData` hashes.
    return hashObject(graphData) + hashObject(opts) + 'version:6';
  },
);

const getFullAssetLayout = memoize(layoutAssetGraph, _assetLayoutCacheKey);

const EMPTY_LAYOUT: AssetGraphLayout = {
  width: 0,
  height: 0,
  nodes: {},
  edges: [],
  groups: {},
};

export const asyncGetFullAssetLayoutIndexDB = indexedDBAsyncMemoize(
  (graphData: GraphData, opts: LayoutAssetGraphOptions) => {
    return new Promise<AssetGraphLayout>((resolve) => {
      const worker = spawnLayoutWorker();
      let didResolveSuccessfully = false;
      worker.onMessage((event) => {
        didResolveSuccessfully = true;
        resolve(event.data);
        worker.terminate();
      });
      worker.onError((error) => {
        console.error(error);
        resolve(EMPTY_LAYOUT);
      });
      worker.onTerminate(() => {
        setTimeout(() => {
          // This timeout is because these workers are used as part of React and end up going through synchronous render loops.
          // This means that the worker can't return any messages until that synchronous loop ends.
          // To ensure at least one synchronous loop ends, we add a timeout 0.
          // This helps us avoid throwing away useful results that were returned faster than the synchronous
          // task we're in.
          if (!didResolveSuccessfully) {
            // Clear the cache entry if the worker is terminated without resolving
            // because the cache entry points to this terminated worker which will never resolve.
            // This makes it so that if we request this layout again, we'll create a new worker
            // and run the layout again.
            asyncGetFullAssetLayoutIndexDB.clearEntry(graphData, opts);
          }
        }, 0);
      });
      worker.postMessage({type: 'layoutAssetGraph', opts, graphData});
    });
  },
  'asyncGetFullAssetLayoutIndexDB',
  _assetLayoutCacheKey,
);

const asyncGetFullAssetLayout = asyncMemoize(
  (graphData: GraphData, opts: LayoutAssetGraphOptions) => {
    return new Promise<AssetGraphLayout>((resolve) => {
      const worker = spawnLayoutWorker();
      worker.onMessage((event) => {
        resolve(event.data);
        worker.terminate();
      });
      worker.onError((error) => {
        console.error(error);
        resolve(EMPTY_LAYOUT);
      });
      worker.postMessage({type: 'layoutAssetGraph', opts, graphData});
    });
  },
  _assetLayoutCacheKey,
);

const spawnLayoutWorker = workerSpawner(
  () => new Worker(new URL('../workers/dagre_layout.worker', import.meta.url)),
);
// Helper Hooks:
// - Automatically switch between sync and async loading strategies
// - Re-layout when the cache key function returns a different value

type State = {
  loading: boolean;
  layout: OpGraphLayout | AssetGraphLayout | null;
  cacheKey: string;
  loadingCacheKey: string | undefined;
};

type Action =
  | {type: 'loading'; payload: {cacheKey: string}}
  | {
      type: 'layout';
      payload: {
        layout: OpGraphLayout | AssetGraphLayout;
        cacheKey: string;
      };
    };

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'loading':
      return {
        loading: true,
        layout: state.layout,
        cacheKey: state.cacheKey,
        loadingCacheKey: action.payload.cacheKey,
      };
    case 'layout':
      return {
        loading: false,
        layout: action.payload.layout,
        cacheKey: action.payload.cacheKey,
        loadingCacheKey:
          state.loadingCacheKey === action.payload.cacheKey ? undefined : state.loadingCacheKey,
      };
    default:
      return state;
  }
};

const initialState: State = {
  loading: false,
  layout: null,
  cacheKey: '',
  loadingCacheKey: undefined,
};

/**
 * Todo: It would be nice to merge these hooks into one, passing the sync + async layout methods in as args.
 * I tried but felt like the complexity wasn't worth the code savings. The key problem is that the layout
 * functions take different args and a generic solution loses the types.
 */

export function useOpLayout(ops: ILayoutOp[], parentOp?: ILayoutOp, forceLargeGraph?: boolean) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const cacheKey = _opLayoutCacheKey(ops, {parentOp});

  const preflightChecks = useMemo(() => {
    const graph = buildGraphDataFromOps(ops);
    return runPreflightChecks(graph);
  }, [ops]);

  const {error, async} = renderingModeForGraph(preflightChecks, forceLargeGraph);

  const requestId = useRef(0);
  const lastRenderedRequestIdRef = useRef(-1);

  useEffect(() => {
    if (error) {
      // Graph is too large to render without an explicit query
      return;
    }
    if (state.cacheKey === cacheKey) {
      // Already have a layout for this cache key, so we can skip re-running the layout.
      return;
    }
    if (state.loadingCacheKey === cacheKey) {
      // Already loading a layout for this cache key, so we can skip re-running the layout.
      return;
    }
    async function runAsyncLayout() {
      const layoutRequestId = requestId.current++;
      dispatch({type: 'loading', payload: {cacheKey}});
      const layout = await asyncGetFullOpLayout(ops, {parentOp});
      if (lastRenderedRequestIdRef.current >= layoutRequestId) {
        // Make sure:
        // 1) We're not rendering a stale layout
        // 2) We render a layout that was requested earlier while a later one is still loading
        return;
      }
      lastRenderedRequestIdRef.current = layoutRequestId;
      dispatch({
        type: 'layout',
        payload: {layout, cacheKey},
      });
    }

    if (!async || typeof window.Worker === 'undefined') {
      const layout = getFullOpLayout(ops, {parentOp});
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, ops, parentOp, async, error, state.cacheKey, state.loadingCacheKey]);

  const loading = !error && (state.loading || !state.layout || state.cacheKey !== cacheKey);

  // Add a UID to create a new dependency whenever the layout inputs change
  useBlockTraceUntilTrue('useAssetLayout', !loading && !!state.layout, {
    uid: cacheKey,
  });

  return {
    loading,
    async,
    error,
    layout: state.layout as OpGraphLayout | null,
  };
}

export function useAssetLayout(
  _graphData: GraphData,
  expandedGroups: string[],
  opts: LayoutAssetGraphOptions,
  dataLoading?: boolean,
) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const graphData = useMemo(() => ({..._graphData, expandedGroups}), [expandedGroups, _graphData]);

  const cacheKey = useMemo(() => _assetLayoutCacheKey(graphData, opts), [graphData, opts]);

  const preflightChecks = useMemo(
    () => runPreflightChecks(graphData, expandedGroups),
    [graphData, expandedGroups],
  );
  const {error, async} = renderingModeForGraph(preflightChecks, opts.forceLargeGraph);

  const requestId = useRef(0);

  const lastRenderedRequestIdRef = useRef(-1);

  useLayoutEffect(() => {
    if (error) {
      return;
    }
    if (dataLoading) {
      // Data is still loading, so we can't run the layout.
      return;
    }
    if (state.cacheKey === cacheKey) {
      // Already have a layout for this cache key, so we can skip re-running the layout.
      return;
    }
    if (state.loadingCacheKey === cacheKey) {
      // Already loading a layout for this cache key, so we can skip re-running the layout.
      return;
    }
    async function runAsyncLayout() {
      const layoutRequestId = requestId.current++;
      dispatch({type: 'loading', payload: {cacheKey}});
      let layout;
      if (CACHING_ENABLED) {
        layout = await asyncGetFullAssetLayoutIndexDB(graphData, opts);
      } else {
        layout = await asyncGetFullAssetLayout(graphData, opts);
      }
      if (lastRenderedRequestIdRef.current >= layoutRequestId) {
        return;
      }
      lastRenderedRequestIdRef.current = layoutRequestId;
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    }

    if (!async) {
      const layout = getFullAssetLayout(graphData, opts);
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, graphData, opts, dataLoading, error, async, state.cacheKey, state.loadingCacheKey]);

  const loading = !error && (state.loading || !state.layout || state.cacheKey !== cacheKey);

  // Add a UID to create a new dependency whenever the layout inputs change
  useBlockTraceUntilTrue('useAssetLayout', !loading && !!state.layout, {
    uid: cacheKey,
  });

  return {
    loading,
    error,
    async,
    layout: state.layout as AssetGraphLayout | null,
  };
}

export {layoutOp} from './layout';
export type {OpGraphLayout, OpLayout, OpLayoutEdge} from './layout';

import memoize from 'lodash/memoize';
import {useEffect, useMemo, useReducer} from 'react';

import {ILayoutOp, LayoutOpGraphOptions, OpGraphLayout, layoutOpGraph} from './layout';
import {useFeatureFlags} from '../app/Flags';
import {asyncMemoize, indexedDBAsyncMemoize} from '../app/Util';
import {GraphData} from '../asset-graph/Utils';
import {AssetGraphLayout, LayoutAssetGraphOptions, layoutAssetGraph} from '../asset-graph/layout';

const ASYNC_LAYOUT_SOLID_COUNT = 50;

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
    const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
    worker.addEventListener('message', (event) => {
      resolve(event.data);
      worker.terminate();
    });
    worker.postMessage({type: 'layoutOpGraph', ops, opts});
  });
}, _opLayoutCacheKey);

// Asset Graph

const _assetLayoutCacheKey = (graphData: GraphData, opts: LayoutAssetGraphOptions) => {
  // Note: The "show secondary edges" toggle means that we need a cache key that incorporates
  // both the displayed nodes and the displayed edges.

  // Make the cache key deterministic by alphabetically sorting all of the keys since the order
  // of the keys is not guaranteed to be consistent even when the graph hasn't changed.

  function recreateObjectWithKeysSorted(obj: Record<string, Record<string, boolean>>) {
    const newObj: Record<string, Record<string, boolean>> = {};
    Object.keys(obj)
      .sort()
      .forEach((key) => {
        newObj[key] = Object.keys(obj[key]!)
          .sort()
          .reduce(
            (acc, k) => {
              acc[k] = obj[key]![k]!;
              return acc;
            },
            {} as Record<string, boolean>,
          );
      });
    return newObj;
  }

  return `${JSON.stringify(opts)}${JSON.stringify({
    version: 2,
    downstream: recreateObjectWithKeysSorted(graphData.downstream),
    upstream: recreateObjectWithKeysSorted(graphData.upstream),
    nodes: Object.keys(graphData.nodes)
      .sort()
      .map((key) => graphData.nodes[key]),
    expandedGroups: graphData.expandedGroups,
  })}`;
};

const getFullAssetLayout = memoize(layoutAssetGraph, _assetLayoutCacheKey);

export const asyncGetFullAssetLayoutIndexDB = indexedDBAsyncMemoize(
  (graphData: GraphData, opts: LayoutAssetGraphOptions) => {
    return new Promise<AssetGraphLayout>((resolve) => {
      const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
      worker.addEventListener('message', (event) => {
        resolve(event.data);
        worker.terminate();
      });
      worker.postMessage({type: 'layoutAssetGraph', opts, graphData});
    });
  },
  _assetLayoutCacheKey,
);

const asyncGetFullAssetLayout = asyncMemoize(
  (graphData: GraphData, opts: LayoutAssetGraphOptions) => {
    return new Promise<AssetGraphLayout>((resolve) => {
      const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
      worker.addEventListener('message', (event) => {
        resolve(event.data);
        worker.terminate();
      });
      worker.postMessage({type: 'layoutAssetGraph', opts, graphData});
    });
  },
  _assetLayoutCacheKey,
);

// Helper Hooks:
// - Automatically switch between sync and async loading strategies
// - Re-layout when the cache key function returns a different value

type State = {
  loading: boolean;
  layout: OpGraphLayout | AssetGraphLayout | null;
  cacheKey: string;
};

type Action =
  | {type: 'loading'}
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
      return {loading: true, layout: null, cacheKey: ''};
    case 'layout':
      return {
        loading: false,
        layout: action.payload.layout,
        cacheKey: action.payload.cacheKey,
      };
    default:
      return state;
  }
};

const initialState: State = {
  loading: false,
  layout: null,
  cacheKey: '',
};

/**
 * Todo: It would be nice to merge these hooks into one, passing the sync + async layout methods in as args.
 * I tried but felt like the complexity wasn't worth the code savings. The key problem is that the layout
 * functions take different args and a generic solution loses the types.
 */

export function useOpLayout(ops: ILayoutOp[], parentOp?: ILayoutOp) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const cacheKey = _opLayoutCacheKey(ops, {parentOp});
  const runAsync = ops.length >= ASYNC_LAYOUT_SOLID_COUNT;

  useEffect(() => {
    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncGetFullOpLayout(ops, {parentOp});
      dispatch({
        type: 'layout',
        payload: {layout, cacheKey},
      });
    }

    if (!runAsync) {
      const layout = getFullOpLayout(ops, {parentOp});
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, ops, parentOp, runAsync]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: runAsync,
    layout: state.layout as OpGraphLayout | null,
  };
}

export function useAssetLayout(
  _graphData: GraphData,
  expandedGroups: string[],
  opts: LayoutAssetGraphOptions,
) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const flags = useFeatureFlags();

  const graphData = useMemo(() => ({..._graphData, expandedGroups}), [expandedGroups, _graphData]);

  const cacheKey = _assetLayoutCacheKey(graphData, opts);
  const nodeCount = Object.keys(graphData.nodes).length;
  const runAsync = nodeCount >= ASYNC_LAYOUT_SOLID_COUNT;

  useEffect(() => {
    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      let layout;
      if (CACHING_ENABLED) {
        layout = await asyncGetFullAssetLayoutIndexDB(graphData, opts);
      } else {
        layout = await asyncGetFullAssetLayout(graphData, opts);
      }
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    }

    if (!runAsync) {
      const layout = getFullAssetLayout(graphData, opts);
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, graphData, runAsync, flags, opts]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: runAsync,
    layout: state.layout as AssetGraphLayout | null,
  };
}

export {layoutOp} from './layout';
export type {OpGraphLayout, OpLayout, OpLayoutEdge} from './layout';

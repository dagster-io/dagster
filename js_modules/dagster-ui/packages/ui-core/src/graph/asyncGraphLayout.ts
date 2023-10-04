import memoize from 'lodash/memoize';
import React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {asyncMemoize, indexedDBAsyncMemoize} from '../app/Util';
import {GraphData} from '../asset-graph/Utils';
import {AssetGraphLayout, LayoutAssetGraphOptions, layoutAssetGraph} from '../asset-graph/layout';

import {ILayoutOp, layoutOpGraph, LayoutOpGraphOptions, OpGraphLayout} from './layout';

const ASYNC_LAYOUT_SOLID_COUNT = 50;

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

const _assetLayoutCacheKey = (graphData: GraphData) => {
  // Note: The "show secondary edges" toggle means that we need a cache key that incorporates
  // both the displayed nodes and the displayed edges.
  return JSON.stringify({
    downstream: graphData.downstream,
    upstream: graphData.upstream,
    nodes: Object.keys(graphData),
  });
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
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const cacheKey = _opLayoutCacheKey(ops, {parentOp});
  const runAsync = ops.length >= ASYNC_LAYOUT_SOLID_COUNT;

  React.useEffect(() => {
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

export function useAssetLayout(graphData: GraphData) {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const flags = useFeatureFlags();

  const cacheKey = _assetLayoutCacheKey(graphData);
  const nodeCount = Object.keys(graphData.nodes).length;
  const runAsync = nodeCount >= ASYNC_LAYOUT_SOLID_COUNT;

  const {flagDisableDAGCache} = useFeatureFlags();

  React.useEffect(() => {
    const opts = {horizontalDAGs: flags.flagHorizontalDAGs};

    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      let layout;
      if (!flagDisableDAGCache) {
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
  }, [cacheKey, graphData, runAsync, flags, flagDisableDAGCache]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: runAsync,
    layout: state.layout as AssetGraphLayout | null,
  };
}

export {layoutOp} from './layout';
export type {OpGraphLayout, OpLayout, OpLayoutEdge} from './layout';

import memoize from 'lodash/memoize';
import React from 'react';

import {asyncMemoize} from '../app/Util';
import {GraphData} from '../asset-graph/Utils';
import {AssetGraphLayout, layoutAssetGraph} from '../asset-graph/layout';

import {ILayoutOp, layoutOpGraph, OpGraphLayout} from './layout';

// Loads the web worker using the Webpack loader `worker-loader`, specifying the import inline.
// This allows us to use web workers without ejecting from `create-react-app` (in order to use the
// config).  We need both worker-loader (wraps the worker code) and babel-loader (transpiles from
// TypeScript to target ES5) in order to keep worker code in sync with our existing libraries.

const ASYNC_LAYOUT_SOLID_COUNT = 50;

// Op Graph

const _opLayoutCacheKey = (ops: ILayoutOp[], parentOp?: ILayoutOp) => {
  const solidKey = ops.map((x) => x.name).join('|');
  const parentKey = parentOp?.name;
  return `${solidKey}:${parentKey}`;
};

export const getFullOpLayout = memoize(layoutOpGraph, _opLayoutCacheKey);

export const asyncGetFullOpLayout = asyncMemoize((ops: ILayoutOp[], parentOp?: ILayoutOp) => {
  return new Promise<OpGraphLayout>((resolve) => {
    const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
    worker.addEventListener('message', (event) => {
      resolve(event.data);
      worker.terminate();
    });
    worker.postMessage({type: 'layoutOpGraph', ops, parentOp});
  });
}, _opLayoutCacheKey);

// Asset Graph

const _assetLayoutCacheKey = (graphData: GraphData) => {
  return Object.keys(graphData.nodes).sort().join('|');
};

export const getFullAssetLayout = memoize(layoutAssetGraph, _assetLayoutCacheKey);

export const asyncGetFullAssetLayout = asyncMemoize((graphData: GraphData) => {
  return new Promise<OpGraphLayout>((resolve) => {
    const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
    worker.addEventListener('message', (event) => {
      resolve(event.data);
      worker.terminate();
    });
    worker.postMessage({type: 'layoutAssetGraph', graphData});
  });
}, _assetLayoutCacheKey);

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
  | {type: 'layout'; payload: {layout: OpGraphLayout | AssetGraphLayout; cacheKey: string}};

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

  const cacheKey = _opLayoutCacheKey(ops, parentOp);

  React.useEffect(() => {
    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncGetFullOpLayout(ops, parentOp);
      dispatch({
        type: 'layout',
        payload: {layout: layout, cacheKey},
      });
    }

    if (ops.length < ASYNC_LAYOUT_SOLID_COUNT) {
      const layout = getFullOpLayout(ops, parentOp);
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, ops, parentOp]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: ops.length >= ASYNC_LAYOUT_SOLID_COUNT,
    layout: state.layout as OpGraphLayout | null,
  };
}

export function useAssetLayout(graphData: GraphData) {
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const cacheKey = _assetLayoutCacheKey(graphData);

  React.useEffect(() => {
    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncGetFullAssetLayout(graphData);
      dispatch({
        type: 'layout',
        payload: {layout: layout, cacheKey},
      });
    }

    if (Object.keys(graphData.nodes).length < ASYNC_LAYOUT_SOLID_COUNT) {
      const layout = getFullAssetLayout(graphData);
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, graphData]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: Object.keys(graphData.nodes).length >= ASYNC_LAYOUT_SOLID_COUNT,
    layout: state.layout as AssetGraphLayout | null,
  };
}

export {layoutOp} from './layout';
export type {OpGraphLayout, OpLayout, ILayout, OpLayoutEdge, IPoint} from './layout';

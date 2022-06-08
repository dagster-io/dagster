import memoize from 'lodash/memoize';
import React from 'react';

import {AppContext} from '../app/AppContext';
import {asyncMemoize} from '../app/Util';
import {GraphData} from '../asset-graph/Utils';
import {AssetGraphLayout, layoutAssetGraph} from '../asset-graph/layout';

import {ILayoutOp, layoutOpGraph, OpGraphLayout} from './layout';

const ASYNC_LAYOUT_SOLID_COUNT = 50;

// Op Graph

const _opLayoutCacheKey = (ops: ILayoutOp[], parentOp?: ILayoutOp) => {
  const solidKey = ops.map((x) => x.name).join('|');
  const parentKey = parentOp?.name;
  return `${solidKey}:${parentKey}`;
};

export const getFullOpLayout = memoize(layoutOpGraph, _opLayoutCacheKey);

export const asyncGetFullOpLayout = asyncMemoize(
  (ops: ILayoutOp[], parentOp?: ILayoutOp, staticPathRoot?: string) => {
    return new Promise<OpGraphLayout>((resolve) => {
      const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
      worker.addEventListener('message', (event) => {
        resolve(event.data);
        worker.terminate();
      });
      worker.postMessage({type: 'layoutOpGraph', ops, parentOp, staticPathRoot});
    });
  },
  _opLayoutCacheKey,
);

// Asset Graph

const _assetLayoutCacheKey = (graphData: GraphData) => {
  // Note: The "show secondary edges" toggle means that we need a cache key that incorporates
  // both the displayed nodes and the displayed edges.
  return JSON.stringify(graphData);
};

export const getFullAssetLayout = memoize(layoutAssetGraph, _assetLayoutCacheKey);

export const asyncGetFullAssetLayout = asyncMemoize(
  (graphData: GraphData, staticPathRoot?: string) => {
    return new Promise<AssetGraphLayout>((resolve) => {
      const worker = new Worker(new URL('../workers/dagre_layout.worker', import.meta.url));
      worker.addEventListener('message', (event) => {
        resolve(event.data);
        worker.terminate();
      });
      worker.postMessage({type: 'layoutAssetGraph', graphData, staticPathRoot});
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
  const {staticPathRoot} = React.useContext(AppContext);

  const cacheKey = _opLayoutCacheKey(ops, parentOp);
  const runAsync = ops.length >= ASYNC_LAYOUT_SOLID_COUNT;

  React.useEffect(() => {
    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncGetFullOpLayout(ops, parentOp, staticPathRoot);
      dispatch({
        type: 'layout',
        payload: {layout, cacheKey},
      });
    }

    if (!runAsync) {
      const layout = getFullOpLayout(ops, parentOp);
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, ops, parentOp, runAsync, staticPathRoot]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: runAsync,
    layout: state.layout as OpGraphLayout | null,
  };
}

export function useAssetLayout(graphData: GraphData) {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {staticPathRoot} = React.useContext(AppContext);

  const cacheKey = _assetLayoutCacheKey(graphData);
  const nodeCount = Object.keys(graphData.nodes).length;
  const runAsync = nodeCount >= ASYNC_LAYOUT_SOLID_COUNT;

  React.useEffect(() => {
    async function runAsyncLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncGetFullAssetLayout(graphData, staticPathRoot);
      dispatch({
        type: 'layout',
        payload: {layout, cacheKey},
      });
    }

    if (!runAsync) {
      const layout = getFullAssetLayout(graphData);
      dispatch({type: 'layout', payload: {layout, cacheKey}});
    } else {
      void runAsyncLayout();
    }
  }, [cacheKey, graphData, runAsync, staticPathRoot]);

  return {
    loading: state.loading || !state.layout || state.cacheKey !== cacheKey,
    async: runAsync,
    layout: state.layout as AssetGraphLayout | null,
  };
}

export {layoutOp} from './layout';
export type {OpGraphLayout, OpLayout, OpLayoutEdge} from './layout';

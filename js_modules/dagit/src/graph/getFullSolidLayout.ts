// eslint-disable-next-line import/no-webpack-loader-syntax
import LayoutWorker from 'worker-loader!babel-loader!../workers/dagre_layout.worker';

import {asyncMemoize, memoize} from '../Util';

import {ILayoutSolid, layoutPipeline} from './layout';

// Loads the web worker using the Webpack loader `worker-loader`, specifying the import inline.
// This allows us to use web workers without ejecting from `create-react-app` (in order to use the
// config).  We need both worker-loader (wraps the worker code) and babel-loader (transpiles from
// TypeScript to target ES5) in order to keep worker code in sync with our existing libraries.

const _layoutCacheKey = (solids: ILayoutSolid[], parentSolid?: ILayoutSolid) => {
  const solidKey = solids.map((x) => x.name).join('|');
  const parentKey = parentSolid?.name;
  return `${solidKey}:${parentKey}`;
};

export const getDagrePipelineLayout = memoize(layoutPipeline, _layoutCacheKey);

const _asyncDagrePipelineLayout = (solids: ILayoutSolid[], parentSolid?: ILayoutSolid) => {
  return new Promise((resolve) => {
    const worker = new LayoutWorker();
    worker.addEventListener('message', function (event) {
      resolve(event.data);
      worker.terminate();
    });
    worker.postMessage({solids, parentSolid});
  });
};

export const asyncDagrePipelineLayout = asyncMemoize(_asyncDagrePipelineLayout, _layoutCacheKey);

export * from './layout';

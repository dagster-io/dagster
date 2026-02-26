import {createWorkerThread} from '@shared/workers/WorkerThread';

import {layoutAssetGraph} from '../asset-graph/layout';
import {layoutOpGraph} from '../graph/layout';
/**
 * NOTE: Please avoid adding React as a transitive dependency to this file, as it can break
 * the development workflow. https://github.com/pmmmwh/react-refresh-webpack-plugin/issues/24
 *
 * If you see an error like `$RefreshReg$ is not defined` during development, check the
 * dependencies of this file. If you find that React has been included as a dependency, please
 * try to remove it.
 */

createWorkerThread(
  async (postMessage: (message: any) => void, data: any) => {
    switch (data.type) {
      case 'layoutOpGraph': {
        const {ops, opts} = data;
        postMessage(layoutOpGraph(ops, opts));
        break;
      }
      case 'layoutAssetGraph': {
        const {graphData, opts} = data;
        postMessage(layoutAssetGraph(graphData, opts));
      }
    }
  },
  (_postMessage: (message: any) => void, error: Error) => {
    console.error(error);
  },
);

/* eslint-disable no-restricted-globals */

/**
 * NOTE: Please avoid adding React as a transitive dependency to this file, as it can break
 * the development workflow. https://github.com/pmmmwh/react-refresh-webpack-plugin/issues/24
 *
 * If you see an error like `$RefreshReg$ is not defined` during development, check the
 * dependencies of this file. If you find that React has been included as a dependency, please
 * try to remove it.
 */

self.addEventListener('message', (event) => {
  const {data} = event;

  // Before we attempt any imports, manually set the Webpack public path to the static path root.
  // This allows us to import paths when a path-prefix value has been set.
  if (data.staticPathRoot) {
    (self as any).__webpack_public_path__ = data.staticPathRoot;
  }

  switch (data.type) {
    case 'layoutOpGraph': {
      import('../graph/layout').then(({layoutOpGraph}) => {
        const {ops, opts} = data;
        self.postMessage(layoutOpGraph(ops, opts));
      });
      break;
    }
    case 'layoutAssetGraph': {
      import('../asset-graph/layout').then(({layoutAssetGraph}) => {
        const {graphData, opts} = data;
        self.postMessage(layoutAssetGraph(graphData, opts));
      });
    }
  }
});

export {};

/**
 * This file must be the first import in the application entry file.
 * https://webpack.js.org/guides/public-path/#on-the-fly
 */

import {extractInitializationData} from './extractInitializationData';

const extracted = extractInitializationData();

// Set the webpack path prefix based on DOM value. This will be used
// for dynamically loaded bundles.
if (typeof extracted.pathPrefix === 'string') {
  __webpack_public_path__ = `${extracted.pathPrefix}/`;
}

export {};

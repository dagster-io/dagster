import * as React from 'react';

import {DeploymentStatusType} from '../instance/DeploymentStatusProvider';

export type AppContextValue = {
  // `basePath` is the root used for routing and GraphQL requests. In open source Dagit,
  // this will also be the same as the root for static assets, `staticPathRoot`.
  basePath: string;
  rootServerURI: string;
  // `staticPathRoot` is the root where static assets are served from. In open source Dagit,
  // this value will be essentially the same as `basePath`, e.g. `${basePath}/`. Setting this
  // value in context allows us to set __webpack_public_path__ for WebWorkers, thereby allowing
  // WebWorkers to import other files.
  staticPathRoot?: string;
  telemetryEnabled: boolean;
  statusPolling?: Set<DeploymentStatusType>;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  rootServerURI: '',
  staticPathRoot: '/',
  telemetryEnabled: false,
});

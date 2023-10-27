import * as React from 'react';

import {DeploymentStatusType} from '../instance/DeploymentStatusProvider';

export type AppContextValue = {
  // `basePath` is the root used for routing and GraphQL requests.
  basePath: string;
  rootServerURI: string;
  telemetryEnabled: boolean;
  statusPolling?: Set<DeploymentStatusType>;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
});

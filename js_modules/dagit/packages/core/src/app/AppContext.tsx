import * as React from 'react';

export type AppContextValue = {
  basePath: string;
  rootServerURI: string;
  telemetryEnabled: boolean;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
});

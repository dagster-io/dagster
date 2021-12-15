import * as React from 'react';

export type AppContextValue = {
  basePath: string;
  rootServerURI: string;
  telemetryEnabled: boolean;
  setTemporaryHeader: (key: string, value: string | undefined) => void;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
  setTemporaryHeader: () => {},
});

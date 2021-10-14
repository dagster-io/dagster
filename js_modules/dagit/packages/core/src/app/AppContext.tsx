import * as React from 'react';

export type AppContextValue = {
  basePath: string;
  rootServerURI: string;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  rootServerURI: '',
});

import * as React from 'react';

type AppContext = {
  basePath: string;
  rootServerURI: string;
  websocketURI: string;
};

export const AppContext = React.createContext<AppContext>({
  basePath: '',
  rootServerURI: '',
  websocketURI: '',
});

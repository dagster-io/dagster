import * as React from 'react';

import {Permissions} from './Permissions';

export type AppContextValue = {
  basePath: string;
  permissions: Permissions;
  rootServerURI: string;
  websocketURI: string;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  permissions: {},
  rootServerURI: '',
  websocketURI: '',
});

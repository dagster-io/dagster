import * as React from 'react';

import {Permissions} from './Permissions';

type AppContext = {
  basePath: string;
  permissions: Permissions;
  rootServerURI: string;
  websocketURI: string;
};

export const AppContext = React.createContext<AppContext>({
  basePath: '',
  permissions: {},
  rootServerURI: '',
  websocketURI: '',
});

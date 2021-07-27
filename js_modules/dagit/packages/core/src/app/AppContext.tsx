import * as React from 'react';

import {PermissionsFromJSON} from './Permissions';

export type AppContextValue = {
  basePath: string;
  permissions: PermissionsFromJSON;
  rootServerURI: string;
};

export const AppContext = React.createContext<AppContextValue>({
  basePath: '',
  permissions: {},
  rootServerURI: '',
});

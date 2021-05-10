import * as React from 'react';

import {AppContext} from './AppContext';
import {PERMISSIONS_ALLOW_ALL} from './Permissions';

const testValue = {
  basePath: '',
  permissions: PERMISSIONS_ALLOW_ALL,
  rootServerURI: '',
  websocketURI: 'ws://foo',
};

export const TestAppContextProvider: React.FC = (props) => (
  <AppContext.Provider value={testValue}>{props.children}</AppContext.Provider>
);

import * as React from 'react';

import {AppContext} from './AppContext';

const testValue = {
  basePath: '',
  rootServerURI: '',
  websocketURI: 'ws://foo',
};

export const TestAppContextProvider: React.FC = (props) => (
  <AppContext.Provider value={testValue}>{props.children}</AppContext.Provider>
);

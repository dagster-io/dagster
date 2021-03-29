import {App, AppProvider} from '@dagit/core';
import * as React from 'react';
import ReactDOM from 'react-dom';

ReactDOM.render(
  <AppProvider>
    <App />
  </AppProvider>,
  document.getElementById('root'),
);

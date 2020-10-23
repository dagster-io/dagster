import '@blueprintjs/core/lib/css/blueprint.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/select/lib/css/blueprint-select.css';
import '@blueprintjs/table/lib/css/table.css';

import 'src/fonts/fonts.css';

import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {createGlobalStyle} from 'styled-components/macro';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  body {
    font-family: sans-serif;
  }

  body ul, body li {
    margin: 0;
  }
`;

// Global decorator to apply the styles to all stories
export const decorators = [
  (Story) => (
    <MemoryRouter>
      <GlobalStyle />
      <Story />
    </MemoryRouter>
  ),
];

export const parameters = {
  actions: {argTypesRegex: '^on[A-Z].*'},
};

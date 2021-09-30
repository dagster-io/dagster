import '@blueprintjs/core/lib/css/blueprint.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/select/lib/css/blueprint-select.css';
import '@blueprintjs/table/lib/css/table.css';
import '@blueprintjs/popover2/lib/css/blueprint-popover2.css';

import {FontFamily} from '../src/ui/styles';

import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {createGlobalStyle} from 'styled-components/macro';

import {GlobalPopoverStyle} from '../src/ui/Popover';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
    -webkit-font-smoothing: antialiased;
  }

  body, input, textarea, button, select {
    font-family: ${FontFamily.default};
  }

  body ul, body li {
    margin: 0;
  }

  .material-icons {
    display: block;
  }
`;

// Global decorator to apply the styles to all stories
export const decorators = [
  (Story) => (
    <MemoryRouter>
      <GlobalStyle />
      <GlobalPopoverStyle />
      <Story />
    </MemoryRouter>
  ),
];

export const parameters = {
  actions: {argTypesRegex: '^on[A-Z].*'},
};

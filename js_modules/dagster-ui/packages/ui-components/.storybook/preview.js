import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';
import {createGlobalStyle} from 'styled-components/macro';

import {
  FontFamily,
  GlobalDialogStyle,
  GlobalInconsolata,
  GlobalInter,
  GlobalPopoverStyle,
  GlobalSuggestStyle,
  GlobalToasterStyle,
  GlobalTooltipStyle,
} from '../src';
import {
  colorBackgroundDefault,
  colorLinkDefault,
  colorTextDefault,
  colorTextLight,
} from '../src/theme/color';
import './blueprint.css';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body {
    background-color: ${colorBackgroundDefault()};
    color: ${colorTextDefault()};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a,
  a:hover,
  a:active {
    color: ${colorLinkDefault()};
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, input, select, textarea {
    background-color: ${colorBackgroundDefault()};
    color: ${colorTextDefault()};
    font-family: ${FontFamily.default};
  }

  button {
    font-family: inherit;
  }

  code, pre {
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }

  input::placeholder {
    color: ${colorTextLight()};
  }
`;

// Global decorator to apply the styles to all stories
export const decorators = [
  (Story) => (
    <MemoryRouter>
      <GlobalStyle />
      <GlobalInter />
      <GlobalInconsolata />
      <GlobalToasterStyle />
      <GlobalTooltipStyle />
      <GlobalPopoverStyle />
      <GlobalDialogStyle />
      <GlobalSuggestStyle />
      <Story />
    </MemoryRouter>
  ),
];

export const parameters = {
  parameters: {
    actions: {argTypesRegex: '^on[A-Z].*'},
  },
};

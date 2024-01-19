import {
  FontFamily,
  GlobalInter,
  GlobalInconsolata,
  GlobalDialogStyle,
  GlobalPopoverStyle,
  GlobalSuggestStyle,
  GlobalToasterStyle,
  GlobalTooltipStyle,
  Color,
} from '../src';

import {MemoryRouter} from 'react-router-dom';

import {createGlobalStyle} from 'styled-components/macro';

import './blueprint.css';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body {
    background-color: ${Color.backgroundDefault()};
    color: ${Color.textDefault()};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a,
  a:hover,
  a:active {
    color: ${Color.linkDefault()};
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, input, select, textarea {
    background-color: ${Color.backgroundDefault()};
    color: ${Color.textDefault()};
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
    color: ${Colors.textLight()};
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

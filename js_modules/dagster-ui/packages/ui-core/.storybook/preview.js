import {
  FontFamily,
  GlobalGeist,
  GlobalGeistMono,
  GlobalDialogStyle,
  GlobalPopoverStyle,
  GlobalSuggestStyle,
  GlobalThemeStyle,
  GlobalTooltipStyle,
  Colors,
  Toaster,
} from '@dagster-io/ui-components';

import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';
import {withThemeByClassName} from '@storybook/addon-themes';

import {createGlobalStyle} from 'styled-components';

import '../src/app/blueprint.css';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body {
    color-scheme: ${Colors.browserColorScheme()};
    background-color: ${Colors.backgroundDefault()};
    color: ${Colors.textDefault()};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a,
  a:hover,
  a:active {
    color: ${Colors.linkDefault()};
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, input, select, textarea {
    background-color: ${Colors.backgroundDefault()};
    color: ${Colors.textDefault()};
    font-family: ${FontFamily.default};
  }

  button {
    font-family: inherit;
  }

  code, pre {
    font-family: ${FontFamily.monospace};
    font-size: 14px;
    font-variant-ligatures: none;
  }
`;

// Global decorator to apply the styles to all stories
export const decorators = [
  (Story) => (
    <MemoryRouter>
      <GlobalStyle />
      <GlobalThemeStyle />
      <GlobalGeist />
      <GlobalGeistMono />
      <GlobalTooltipStyle />
      <GlobalPopoverStyle />
      <GlobalDialogStyle />
      <GlobalSuggestStyle />
      <Toaster richColors />
      <Story />
    </MemoryRouter>
  ),
  withThemeByClassName({
    themes: {
      light: 'themeLight',
      dark: 'themeDark',
      system: 'themeSystem',
      lightNoRedGreen: 'themeLightNoRedGreen',
      darkNoRedGreen: 'themeDarkNoRedGreen',
      systemNoRedGreen: 'themeSystemNoRedGreen',
    },
    defaultTheme: 'system',
    parentSelector: 'body',
  }),
];

export const parameters = {};

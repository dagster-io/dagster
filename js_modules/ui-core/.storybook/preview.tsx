import {Toaster} from '@dagster-io/ui-components';
import {withThemeByClassName} from '@storybook/addon-themes';
import {MemoryRouter} from 'react-router-dom';

import '@dagster-io/ui-components/css/theme.css';

// Global decorator to apply the styles to all stories
export const decorators = [
  (Story) => (
    <MemoryRouter>
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

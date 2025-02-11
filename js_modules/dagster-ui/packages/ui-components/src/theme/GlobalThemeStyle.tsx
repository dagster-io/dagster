import {createGlobalStyle} from 'styled-components';

import {darkHighContrastThemeColors} from './darkHighContrastThemeColors';
import {darkThemeColors} from './darkThemeColors';
import {lightHighContrastThemeColors} from './lightHighContrastThemeColors';
import {lightThemeColors} from './lightThemeColors';
import {CoreColorStyles} from '../palettes/CoreColorStyles';
import {DataVizColorStyles} from '../palettes/DataVizColorStyles';
import {TranslucentColorStyles} from '../palettes/TranslucentColorStyles';

const ThemeRoot = createGlobalStyle`
  @media (prefers-color-scheme: light) {
    :root, .themeSystem {
      ${lightThemeColors}
    }

    .themeSystemHighContrast {
      ${lightHighContrastThemeColors}
    }
  }

  @media (prefers-color-scheme: dark) {
    :root, .themeSystem {
      ${darkThemeColors}
    }

    .themeSystemHighContrast {
      ${darkHighContrastThemeColors}
    }
  }

  .themeLight {
    ${lightThemeColors}
  }

  .themeLightHighContrast {
    ${lightHighContrastThemeColors}
  }

  .themeDark {
    ${darkThemeColors}
  }

  .themeDarkHighContrast {
    ${darkHighContrastThemeColors}
  }
`;

export const GlobalThemeStyle = () => {
  return (
    <>
      <CoreColorStyles />
      <TranslucentColorStyles />
      <DataVizColorStyles />
      <ThemeRoot />
    </>
  );
};

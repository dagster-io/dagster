import {createGlobalStyle} from 'styled-components';

import {darktNoRedGreenThemeColors} from './darkNoRedGreenThemeColors';
import {darkThemeColors} from './darkThemeColors';
import {lightNoRedGreenThemeColors} from './lightNoRedGreenThemeColors';
import {lightThemeColors} from './lightThemeColors';
import {CoreColorStyles} from '../palettes/CoreColorStyles';
import {DataVizColorStyles} from '../palettes/DataVizColorStyles';
import {TranslucentColorStyles} from '../palettes/TranslucentColorStyles';

const ThemeRoot = createGlobalStyle`
  @media (prefers-color-scheme: light) {
    :root, .themeSystem {
      ${lightThemeColors}
    }

    .themeSystemNoRedGreen {
      ${lightNoRedGreenThemeColors}
    }
  }

  @media (prefers-color-scheme: dark) {
    :root, .themeSystem {
      ${darkThemeColors}
    }

    .themeSystemNoRedGreen {
      ${darktNoRedGreenThemeColors}
    }
  }

  .themeLight {
    ${lightThemeColors}
  }

  .lightNoRedGreenThemeColors {
    ${lightNoRedGreenThemeColors}
  }

  .themeDark {
    ${darkThemeColors}
  }

  .darktNoRedGreenThemeColors {
    ${darktNoRedGreenThemeColors}
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

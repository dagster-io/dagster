import {createGlobalStyle} from 'styled-components';

import {darkNoRedGreenThemeColors} from './darkNoRedGreenThemeColors';
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
      ${darkNoRedGreenThemeColors}
    }
  }

  .themeLight {
    ${lightThemeColors}
  }

  .themeLightNoRedGreen {
    ${lightNoRedGreenThemeColors}
  }

  .themeDark {
    ${darkThemeColors}
  }

  .themeDarkNoRedGreen {
    ${darkNoRedGreenThemeColors}
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

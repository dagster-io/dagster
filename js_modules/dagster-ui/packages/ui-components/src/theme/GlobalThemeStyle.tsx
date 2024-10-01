import {createGlobalStyle} from 'styled-components';

import {darkThemeColors} from './darkThemeColors';
import {lightThemeColors} from './lightThemeColors';
import {CoreColorStyles} from '../palettes/CoreColorStyles';
import {DataVizColorStyles} from '../palettes/DataVizColorStyles';
import {TranslucentColorStyles} from '../palettes/TranslucentColorStyles';

const ThemeRoot = createGlobalStyle`
  @media (prefers-color-scheme: light) {
    :root, .themeSystem {
      ${lightThemeColors}
    }
  }

  @media (prefers-color-scheme: dark) {
    :root, .themeSystem {
      ${darkThemeColors}
    }
  }

  .themeLight {
    ${lightThemeColors}
  }

  .themeDark {
    ${darkThemeColors}
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

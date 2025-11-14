import {createGlobalStyle} from 'styled-components';

import {darkNoRedGreenThemeColors} from './darkNoRedGreenThemeColors';
import {darkThemeColors} from './darkThemeColors';
import {lightNoRedGreenThemeColors} from './lightNoRedGreenThemeColors';
import {lightThemeColors} from './lightThemeColors';
import {CoreColorStyles} from '../palettes/CoreColorStyles';
import {DataVizColorStyles} from '../palettes/DataVizColorStyles';
import {TranslucentColorStyles} from '../palettes/TranslucentColorStyles';

const ThemeRoot = createGlobalStyle`
  :root {
    --font-default: Geist, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Open Sans, Helvetica Neue, Icons16, sans-serif;
    --font-mono: Geist Mono, Roboto Mono, SF Mono, SFMono-Regular, ui-monospace, Source Code Pro,
      Menlo, Monaco, Cascadia Mono, Segoe UI Mono, Oxygen Mono, Ubuntu Monospace, Fira Mono,
      Droid Sans Mono, Courier New, monospace;
    }
  }
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

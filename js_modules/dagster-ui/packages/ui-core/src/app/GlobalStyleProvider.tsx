import {
  Colors,
  FontFamily,
  GlobalDialogStyle,
  GlobalGeist,
  GlobalGeistMono,
  GlobalPopoverStyle,
  GlobalSuggestStyle,
  GlobalThemeStyle,
  GlobalToasterStyle,
  GlobalTooltipStyle,
  themeToClassName,
} from '@dagster-io/ui-components';
import {useLayoutEffect} from 'react';
import {createGlobalStyle} from 'styled-components';

import {GlobalCustomAlertPortalStyle} from './CustomAlertProvider';
import {useThemeState} from './useThemeState';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    color-scheme: ${Colors.browserColorScheme()};
    background-color: ${Colors.backgroundDefault()};
    color: ${Colors.textDefault()};
    scrollbar-color: ${Colors.accentGrayHover()} ${Colors.backgroundDefault()};
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a,
  a:hover,
  a:active {
    color: ${Colors.linkDefault()};
  }

  #root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, input, select, textarea {
    font-family: ${FontFamily.default};
  }

  button {
    color: ${Colors.textDefault()};
    font-family: inherit;
  }

  code, pre {
    font-family: ${FontFamily.monospace};
    font-size: 14px;
    font-variant-ligatures: none;
  }

  :focus-visible {
    outline: ${Colors.focusRing()} auto 1px;
  }

  :focus:not(:focus-visible) {
    outline: none;
  }

  :not(a):focus,
  :not(a):focus-visible {
    outline-offset: 1px;
  }
`;

export const GlobalStyleProvider = () => {
  const theme = useThemeState();

  // Given a theme setting, apply the appropriate class name to the body to set the
  // desired CSS var values. When the theme changes, the class name is updated.
  useLayoutEffect(() => {
    const allThemeClassNames = new Set(Object.values(themeToClassName));
    const className = themeToClassName[theme];
    allThemeClassNames.delete(className);
    document.body.classList.add(className);
    Array.from(allThemeClassNames).forEach((className) => {
      document.body.classList.remove(className);
    });
  }, [theme]);

  return (
    <>
      <GlobalGeist />
      <GlobalGeistMono />
      <GlobalStyle />
      <GlobalThemeStyle />
      <GlobalToasterStyle />
      <GlobalTooltipStyle />
      <GlobalPopoverStyle />
      <GlobalDialogStyle />
      <GlobalCustomAlertPortalStyle />
      <GlobalSuggestStyle />
    </>
  );
};

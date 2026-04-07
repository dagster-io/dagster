import {themeToClassName} from '@dagster-io/ui-components';
import {useLayoutEffect} from 'react';

import {useThemeState} from './useThemeState';
import '@dagster-io/ui-components/src/css/theme.css';
import './GlobalStyle.css';

export const GlobalStyleProvider = () => {
  const {theme} = useThemeState();

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

  return null;
};

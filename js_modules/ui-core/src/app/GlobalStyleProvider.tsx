import {themeToClassName} from '@dagster-io/ui-components';
import {useLayoutEffect} from 'react';

import {MOBILE_BODY_CLASS} from './layout/LayoutMode';
import {useMobileRouteEnabled} from './layout/mobileRouteStatus';
import {useThemeState} from './useThemeState';
import '@dagster-io/ui-components/src/css/theme.css';
import './GlobalStyle.css';

export const GlobalStyleProvider = () => {
  const {theme} = useThemeState();
  const isMobileRouteEnabled = useMobileRouteEnabled();

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

    // Mobile browsers tint their chrome with `theme-color`; keep it matching the page.
    const themeColor = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
    if (themeColor) {
      themeColor.content = getComputedStyle(document.body)
        .getPropertyValue('--color-background-default')
        .trim();
    }
  }, [theme]);

  // Lets page-level CSS Modules opt into mobile rules with `:global(.dagster-mobile) .foo`.
  // Keyed on the mobile layout, not the layout mode, so desktop pages shown as a fallback on
  // a phone don't pick up mobile rules. Shared components should use @container instead.
  useLayoutEffect(() => {
    document.body.classList.toggle(MOBILE_BODY_CLASS, isMobileRouteEnabled);
  }, [isMobileRouteEnabled]);

  return null;
};

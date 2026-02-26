import {DAGSTER_THEME_KEY, DagsterTheme} from '@dagster-io/ui-components';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const themeSet = new Set([
  DagsterTheme.Light,
  DagsterTheme.Dark,
  DagsterTheme.LightNoRedGreen,
  DagsterTheme.DarkNoRedGreen,
  DagsterTheme.SystemNoRedGreen,
]);

export const useThemeState = () => {
  const [theme, setTheme] = useStateWithStorage<DagsterTheme>(DAGSTER_THEME_KEY, (value: any) => {
    if (themeSet.has(value)) {
      return value;
    }
    return DagsterTheme.System;
  });

  return {theme, setTheme};
};

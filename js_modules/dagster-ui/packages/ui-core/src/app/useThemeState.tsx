import {DAGSTER_THEME_KEY, DagsterTheme} from '@dagster-io/ui-components';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const useThemeState = () => {
  const [theme] = useStateWithStorage<DagsterTheme>(DAGSTER_THEME_KEY, (value: any) => {
    if (value === DagsterTheme.Light || value === DagsterTheme.Dark) {
      return value;
    }
    return DagsterTheme.System;
  });

  return theme;
};

import {DagsterTheme} from '@dagster-io/ui-components';

export const getBrowserColorSchemePreference = () => {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return DagsterTheme.Dark;
  }
  return DagsterTheme.Light;
};

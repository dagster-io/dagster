export enum DagsterTheme {
  Light = 'Light',
  Dark = 'Dark',
  System = 'System',
}

export const themeToClassName = {
  [DagsterTheme.Light]: 'themeLight',
  [DagsterTheme.Dark]: 'themeDark',
  [DagsterTheme.System]: 'themeSystem',
};

export const DAGSTER_THEME_KEY = 'dagster-theme';

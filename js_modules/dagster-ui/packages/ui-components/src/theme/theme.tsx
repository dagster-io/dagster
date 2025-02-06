export enum DagsterTheme {
  Light = 'Light',
  Dark = 'Dark',
  System = 'System',
  LightHighContrast = 'LightHighContrast',
  DarkHighContrast = 'DarkHighContrast',
  SystemHighContrast = 'SystemHighContrast',
}

export const themeToClassName = {
  [DagsterTheme.System]: 'themeSystem',
  [DagsterTheme.Light]: 'themeLight',
  [DagsterTheme.Dark]: 'themeDark',
  [DagsterTheme.LightHighContrast]: 'themeLightHighContrast',
  [DagsterTheme.DarkHighContrast]: 'themeDarkHighContrast',
  [DagsterTheme.SystemHighContrast]: 'themeSystemHighContrast',
};

export const DAGSTER_THEME_KEY = 'dagster-theme';

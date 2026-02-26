export enum DagsterTheme {
  Light = 'Light',
  Dark = 'Dark',
  System = 'System',
  LightNoRedGreen = 'LightNoRedGreen',
  DarkNoRedGreen = 'DarkNoRedGreen',
  SystemNoRedGreen = 'SystemNoRedGreen',
}

export const themeToClassName = {
  [DagsterTheme.System]: 'themeSystem',
  [DagsterTheme.Light]: 'themeLight',
  [DagsterTheme.Dark]: 'themeDark',
  [DagsterTheme.LightNoRedGreen]: 'themeLightNoRedGreen',
  [DagsterTheme.DarkNoRedGreen]: 'themeDarkNoRedGreen',
  [DagsterTheme.SystemNoRedGreen]: 'themeSystemNoRedGreen',
};

export const DAGSTER_THEME_KEY = 'dagster-theme';

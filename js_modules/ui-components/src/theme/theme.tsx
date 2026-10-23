export enum DagsterTheme {
  Light = 'Light',
  Dark = 'Dark',
  System = 'System',
  LightNoRedGreen = 'LightNoRedGreen',
  DarkNoRedGreen = 'DarkNoRedGreen',
  SystemNoRedGreen = 'SystemNoRedGreen',
  Custom1 = 'Custom1',
  AlinosLight = 'AlinosLight',
  AlinosDark = 'AlinosDark',
  Halloween = 'Halloween',
}

export const themeToClassName = {
  [DagsterTheme.System]: 'themeSystem',
  [DagsterTheme.Light]: 'themeLight',
  [DagsterTheme.Dark]: 'themeDark',
  [DagsterTheme.LightNoRedGreen]: 'themeLightNoRedGreen',
  [DagsterTheme.DarkNoRedGreen]: 'themeDarkNoRedGreen',
  [DagsterTheme.SystemNoRedGreen]: 'themeSystemNoRedGreen',
  [DagsterTheme.Custom1]: 'themeCustom1',
  [DagsterTheme.AlinosLight]: 'themeAlinosLight',
  [DagsterTheme.AlinosDark]: 'themeAlinosDark',
  [DagsterTheme.Halloween]: 'themeHalloween',
};

export const DAGSTER_THEME_KEY = 'dagster-theme';

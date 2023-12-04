import memoize from 'lodash/memoize';

import {DarkPalette} from '../palettes/DarkPalette';
import {LegacyPalette} from '../palettes/LegacyPalette';
import {LightPalette} from '../palettes/LightPalette';

export enum DagsterTheme {
  Legacy = 'Legacy',
  Light = 'Light',
  Dark = 'Dark',
}

export const DAGSTER_THEME_KEY = 'dagster-theme';

export const getTheme = memoize(() => {
  const stored = window.localStorage.getItem('dagster-theme');

  let value: string | null = null;

  if (stored) {
    try {
      value = JSON.parse(stored);
    } catch (e) {
      if (typeof stored === 'string') {
        value = stored;
      }
    }
  }

  // Allow setting the theme as an override.
  if (value === DagsterTheme.Light || value === DagsterTheme.Dark) {
    return value;
  }

  // todo dish: Uncomment this to allow OS settings to work automatically.
  // if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
  //   return DagsterTheme.Dark;
  // }

  return DagsterTheme.Legacy;
});

export const getPaletteForTheme = () => {
  const theme = getTheme();
  switch (theme) {
    case DagsterTheme.Dark:
      return DarkPalette;
    case DagsterTheme.Light:
      return LightPalette;
    case DagsterTheme.Legacy:
    default:
      return LegacyPalette;
  }
};

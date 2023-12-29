import memoize from 'lodash/memoize';

import {DarkPalette} from '../palettes/DarkPalette';
import {LightPalette} from '../palettes/LightPalette';
import {assertUnreachable} from '../util/assertUnreachable';

export enum DagsterTheme {
  Light = 'Light',
  Dark = 'Dark',
  System = 'System',
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

  // Use system preference if no choice has been made explicitly.
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return DagsterTheme.Dark;
  }

  return DagsterTheme.Light;
});

export const getPaletteForTheme = () => {
  const theme = getTheme();
  switch (theme) {
    case DagsterTheme.Dark:
      return DarkPalette;
    case DagsterTheme.Light:
      return LightPalette;
    default:
      return assertUnreachable(theme);
  }
};

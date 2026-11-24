import {DagsterTheme} from '@dagster-io/ui-components';

import styles from './css/Snowfall.module.css';
import {useThemeState} from '../app/useThemeState';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

// Snowflakes drifting down the whole screen. Only rendered on the winter
// themes, and can be switched off in user settings.

export const SNOW_THEMES = [DagsterTheme.Christmas, DagsterTheme.Frost];

const SNOW_STORAGE_KEY = 'hillpointe-snowfall';

export const useSnowfallEnabled = () =>
  useStateWithStorage(SNOW_STORAGE_KEY, (value: any) =>
    typeof value === 'boolean' ? value : true,
  );

// Spread out by index rather than at random, so every render gives the same sky.
const FLAKES = Array.from({length: 24}, (_, i) => ({
  left: (i * 37 + 5) % 100, // vw
  size: 3 + (i % 4) * 1.5, // px
  duration: 10 + ((i * 7) % 9), // s
  delay: -((i * 13) % 19), // s; negative, so the sky starts full
}));

export const Snowfall = () => {
  const {theme} = useThemeState();
  const [enabled] = useSnowfallEnabled();

  if (!enabled || !SNOW_THEMES.includes(theme)) {
    return null;
  }

  return (
    <>
      {FLAKES.map((flake, i) => (
        <div
          key={i}
          className={styles.flake}
          style={{
            left: `${flake.left}vw`,
            width: flake.size,
            height: flake.size,
            animationDuration: `${flake.duration}s`,
            animationDelay: `${flake.delay}s`,
          }}
        />
      ))}
    </>
  );
};

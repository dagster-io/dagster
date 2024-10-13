import {colorNameToVar} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';

import {useThemeState} from './useThemeState';

const computeRGBValuesFromBodyStyle = () => {
  const computedStyle = window.getComputedStyle(document.body);
  return Object.fromEntries(
    Object.values(colorNameToVar).map((cssVar) => {
      const strippedVarName = cssVar.replace(/var\(([\w-]+)\)/, '$1');
      const computedRGB = computedStyle.getPropertyValue(strippedVarName);
      return [cssVar, computedRGB];
    }),
  );
};

/**
 * HELLO! This hook is an escape hatch, and you probably don't need it!
 *
 * Based on the computed body style for the current theme, map CSS vars to
 * computed rgba values.
 *
 * In almost all cases, using the `Colors` function is perfectly sufficient,
 * since these provide `var(--...)` strings that work properly in inline styles.
 * That's probably what you want!
 *
 * In some cases -- a major example is Chart.js -- we need to provide RGB values
 * directly to the consuming library. To do so, we compute. When the theme updates,
 * the mapped values do as well.
 */
export const useRGBColorsForTheme = () => {
  const theme = useThemeState();
  const [rgbState, setRGBState] = useState(() => computeRGBValuesFromBodyStyle());

  useEffect(() => {
    const updatedStyles = computeRGBValuesFromBodyStyle();
    setRGBState(updatedStyles);
  }, [theme]);

  return rgbState;
};

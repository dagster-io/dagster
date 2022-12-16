import React from 'react';

export const Colors = {
  Dark: 'var(--Dark);',
  Gray900: 'var(--Gray900)',
  Gray800: 'var(--Gray800)',
  Gray700: 'var(--Gray700)',
  Gray600: 'var(--Gray600)',
  Gray500: 'var(--Gray500)',
  Gray400: 'var(--Gray400)',
  Gray300: 'var(--Gray300)',
  Gray200: 'var(--Gray200)',
  Gray100: 'var(--Gray100)',
  Gray50: 'var(--Gray50)',
  KeylineGray: 'var(--KeylineGray)',
  WashGray: 'var(--WashGray)',
  Gray10: 'var(--Gray10)',
  White: 'var(--White)',
  LightPurple: 'var(--LightPurple)',
  Link: 'var(--Link)',
  Blue700: 'var(--Blue700)',
  Blue500: 'var(--Blue500)',
  Blue200: 'var(--Blue200)',
  Blue100: 'var(--Blue100)',
  Blue50: 'var(--Blue50)',
  Red700: 'var(--Red700)',
  Red500: 'var(--Red500)',
  Red200: 'var(--Red200)',
  Red100: 'var(--Red100)',
  Red50: 'var(--Red50)',
  HighlightRed: 'var(--HighlightRed)',
  Yellow700: 'var(--Yellow700)',
  Yellow500: 'var(--Yellow500)',
  Yellow200: 'var(--Yellow200)',
  Yellow50: 'var(--Yellow50)',
  ForestGreen: 'var(--ForestGreen)',
  Green700: 'var(--Green700)',
  Green500: 'var(--Green500)',
  Green200: 'var(--Green200)',
  Green50: 'var(--Green50)',
  NeonGreen: 'var(--NeonGreen)',
  HighlightGreen: 'var(--HighlightGreen)',
  Olive700: 'var(--Olive700)',
  Olive500: 'var(--Olive500)',
  Olive200: 'var(--Olive200)',
  Olive50: 'var(--Olive50)',
};

export type ColorKey = keyof typeof Colors;

const colorCache: Partial<Record<ColorKey, string>> = {};
const originalColorCache: typeof colorCache = {};

export function resetColorTheme() {
  Object.keys(originalColorCache).forEach((key) => {
    setColorValue(key as ColorKey, originalColorCache[key]);
  });
}

let _cachedGetComputedStyleForDocumentElementValue: null | ReturnType<
  typeof getComputedStyle
> = null;
function cachedGetComputedStyleForDocumentElement() {
  if (!_cachedGetComputedStyleForDocumentElementValue) {
    _cachedGetComputedStyleForDocumentElementValue = getComputedStyle(document.documentElement);
    requestAnimationFrame(() => {
      _cachedGetComputedStyleForDocumentElementValue = null;
    });
  }
  return _cachedGetComputedStyleForDocumentElementValue;
}

export function getColorValue(colorKey: ColorKey): string {
  if (!colorCache[colorKey]) {
    colorCache[colorKey] = cachedGetComputedStyleForDocumentElement()
      .getPropertyValue(`--${colorKey}`)
      .trim();
    if (!originalColorCache[colorKey]) {
      originalColorCache[colorKey] = colorCache[colorKey];
    }
    const customColor = localStorage.getItem(`theme:color:${colorKey}`);
    if (customColor) {
      colorCache[colorKey] = customColor;
    }
  }
  return colorCache[colorKey]!;
}

const listeners: Record<ColorKey, ((value: string) => void)[]> = Object.keys(Colors).reduce(
  (colors, key) => {
    colors[key] = [
      (value: string) => {
        colorCache[key] = value;
      },
    ];
    return colors;
  },
  {} as any,
);

export function setColorValue(colorKey: ColorKey, value: string) {
  if (!originalColorCache[colorKey]) {
    originalColorCache[colorKey] = getColorValue(colorKey);
  }
  localStorage.setItem(`theme:color:${colorKey}`, value);
  document.documentElement.style.setProperty(`--${colorKey}`, value);
  listeners[colorKey].forEach((listener) => {
    listener(value);
  });
}

export function useColorValue(colorKey: ColorKey): string {
  const [color, setColor] = React.useState(getColorValue(colorKey));
  React.useLayoutEffect(() => {
    const listener = (value: string) => {
      setColor(value);
    };
    listeners[colorKey].push(listener);
    return () => {
      const listenerIndex = listeners[colorKey].indexOf(listener);
      if (listenerIndex !== -1) {
        listeners[colorKey].splice(listenerIndex, 1);
      }
    };
  });
  return color;
}

requestAnimationFrame(() => {
  Object.keys(Colors).forEach((key: string) => {
    const colorKey = key as ColorKey;
    setColorValue(colorKey, getColorValue(colorKey));
  });
});

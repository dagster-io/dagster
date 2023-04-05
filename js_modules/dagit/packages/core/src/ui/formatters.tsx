const compactFormatter = new Intl.NumberFormat(navigator.language, {
  compactDisplay: 'short',
  notation: 'compact',
});

export const numberFormatter = new Intl.NumberFormat(navigator.language, {});

export const compactNumber = (num: number | bigint): string => compactFormatter.format(num);

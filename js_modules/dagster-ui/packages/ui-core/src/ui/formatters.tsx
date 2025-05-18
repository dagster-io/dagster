const compactFormatter = new Intl.NumberFormat(navigator.language, {
  compactDisplay: 'short',
  notation: 'compact',
});

export const numberFormatter = new Intl.NumberFormat(navigator.language, {});
export const percentFormatter = new Intl.NumberFormat(navigator.language, {
  style: 'percent',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});
export const compactNumberFormatter = new Intl.NumberFormat(navigator.language, {
  compactDisplay: 'short',
  notation: 'compact',
  maximumFractionDigits: 1,
});

export const compactNumber = (num: number | bigint): string => compactFormatter.format(num);

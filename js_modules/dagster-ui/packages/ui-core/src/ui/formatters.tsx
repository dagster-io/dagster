import {weakMapMemoize} from '../util/weakMapMemoize';

const compactFormatter = new Intl.NumberFormat(navigator.language, {
  compactDisplay: 'short',
  notation: 'compact',
});

export const numberFormatter = new Intl.NumberFormat(navigator.language, {});
export const numberFormatterWithMaxFractionDigits = weakMapMemoize(
  (fractionDigits: number) =>
    new Intl.NumberFormat(navigator.language, {
      maximumFractionDigits: fractionDigits,
    }),
);
export const percentFormatter = new Intl.NumberFormat(navigator.language, {
  style: 'percent',
  minimumFractionDigits: 0,
  maximumFractionDigits: 1,
});
export const compactNumberFormatter = new Intl.NumberFormat(navigator.language, {
  compactDisplay: 'short',
  notation: 'compact',
  maximumFractionDigits: 0,
});

export const compactNumber = (num: number | bigint): string => compactFormatter.format(num);

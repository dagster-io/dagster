import memoize from 'lodash/memoize';

const compactFormatter = memoize(
  () =>
    new Intl.NumberFormat(navigator.language, {
      compactDisplay: 'short',
      notation: 'compact',
    }),
);

export const compactNumber = (num: number | bigint): string => compactFormatter().format(num);

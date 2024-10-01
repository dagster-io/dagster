import {ReportingUnitType} from './types';
import {formatElapsedTimeWithoutMsec} from '../app/Util';
import {compactNumber, numberFormatter} from '../ui/formatters';

type Options = {
  integerFormat?: 'default' | 'compact';
  floatPrecision?: 'placeholder-for-tiny-values' | 'maximum-precision';
  floatFormat?: 'default' | 'compact-above-threshold';
};

const floatFormatter = new Intl.NumberFormat(navigator.language, {
  maximumFractionDigits: 2,
});

const veryPreciseFloatFormatter = new Intl.NumberFormat(navigator.language, {
  maximumFractionDigits: 6,
});

export const TINY_NUMBER_THRESHOLD = 0.01;
export const LARGE_FLOAT_COMPACT_THRESHOLD = 999;

/**
 * Chart.js may have formatted the value. Remove the integer separators so that
 * we can handle formatting ourselves.
 *
 * Replacing only the `,` appears to work correctly even in non-en-US locales.
 * Presumably Chart.js always formats numbers ith en-US formatting.
 */
export const stripFormattingFromNumber = (value: string | number): number => {
  return typeof value === 'number' ? value : parseFloat(value.replace(/[\s,]/g, ''));
};

export const formatMetric = (
  value: string | number,
  unitType: ReportingUnitType,
  options?: Options,
) => {
  const num = stripFormattingFromNumber(value);

  if (unitType === ReportingUnitType.TIME_MS) {
    return formatElapsedTimeWithoutMsec(num);
  }

  // If a float/int value is a "very small" number (based on threshold constant defined
  // above), either show the number of decimal places for maximum precision or show a
  // "placeholder" string ("<0.01")
  if (num > 0 && num < TINY_NUMBER_THRESHOLD) {
    return options?.floatPrecision === 'maximum-precision'
      ? veryPreciseFloatFormatter.format(num)
      : `<${TINY_NUMBER_THRESHOLD}`;
  }

  const compactIfFloat =
    options?.floatFormat === 'compact-above-threshold' && num > LARGE_FLOAT_COMPACT_THRESHOLD;

  if (unitType === ReportingUnitType.FLOAT) {
    return compactIfFloat ? compactNumber(num) : floatFormatter.format(num);
  }

  // The unit type might be expected to be an integer, but if it's an average, the value here
  // might have a decimal value. If so, format it with float formatting.
  const hasDecimal = `${value}`.includes('.');
  if (hasDecimal) {
    return compactIfFloat ? compactNumber(num) : floatFormatter.format(num);
  }

  return options?.integerFormat === 'compact' ? compactNumber(num) : numberFormatter.format(num);
};

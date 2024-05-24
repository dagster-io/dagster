export const COST_PER_UNIT_FORMATTER = new Intl.NumberFormat(navigator.language, {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 6,
});

export const TOTAL_COST_FORMATTER = new Intl.NumberFormat(navigator.language, {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
});

export const COMPACT_COST_FORMATTER = new Intl.NumberFormat(navigator.language, {
  style: 'currency',
  currency: 'USD',
  compactDisplay: 'short',
  notation: 'compact',
});

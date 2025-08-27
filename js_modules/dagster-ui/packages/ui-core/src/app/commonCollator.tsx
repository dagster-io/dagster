export const COMMON_COLLATOR = new Intl.Collator(
  typeof navigator !== 'undefined' ? navigator.language : 'en-US',
  {sensitivity: 'base'},
);

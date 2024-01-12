import memoize from 'lodash/memoize';

export const browserTimezone = memoize(() => Intl.DateTimeFormat().resolvedOptions().timeZone);
export const browserTimezoneAbbreviation = memoize(() => timezoneAbbreviation(browserTimezone()));
export const timezoneAbbreviation = memoize((timeZone: string) => {
  const dateString = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    timeZone,
    timeZoneName: 'short',
  });
  const [_, abbreviation] = dateString.split(', ');
  return abbreviation!;
});
export const automaticLabel = memoize(() => `Automatic (${browserTimezoneAbbreviation()})`);

// Detect the hour cycle based on the presence of a dayPeriod in a formatted time string,
// since the `hourCycle` property on the Intl.Locale object may be undefined.
export const browserHourCycle = memoize(() => {
  const format = new Intl.DateTimeFormat(navigator.language, {timeStyle: 'short'});
  const parts = format.formatToParts(new Date());
  const partKeys = parts.map((part) => part.type);
  return partKeys.includes('dayPeriod') ? 'h12' : 'h23';
});

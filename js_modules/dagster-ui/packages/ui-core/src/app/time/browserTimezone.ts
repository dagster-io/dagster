import memoize from 'lodash/memoize';

// Etc/Unknown states that TZ information cannot be determined based on user's preferences.
// We can't pass this value to `toLocaleDateString`, so we need to handle it and convert it
// to a valid value.
const BROWSER_TZ_UNKNOWN = `Etc/Unknown`;

export const browserTimezone = memoize(() => {
  const {timeZone} = Intl.DateTimeFormat().resolvedOptions();
  if (timeZone === BROWSER_TZ_UNKNOWN) {
    return 'UTC';
  }
  return timeZone;
});

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

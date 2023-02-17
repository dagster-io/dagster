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
  return abbreviation;
});
export const automaticLabel = memoize(() => `Automatic (${browserTimezoneAbbreviation()})`);

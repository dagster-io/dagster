export const browserTimezone = () => Intl.DateTimeFormat().resolvedOptions().timeZone;
export const browserTimezoneAbbreviation = () => timezoneAbbreviation(browserTimezone());
export const timezoneAbbreviation = (timeZone: string) => {
  const dateString = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    timeZone,
    timeZoneName: 'short',
  });
  const [_, abbreviation] = dateString.split(', ');
  return abbreviation;
};
export const automaticLabel = () => `Automatic (${browserTimezoneAbbreviation()})`;

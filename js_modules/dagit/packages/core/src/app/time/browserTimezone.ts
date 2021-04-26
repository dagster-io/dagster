import moment from 'moment-timezone';

export const browserTimezone = () => Intl.DateTimeFormat().resolvedOptions().timeZone;
export const browserTimezoneAbbreviation = () => moment.tz(browserTimezone()).format('z');
export const automaticLabel = () => `Automatic (${browserTimezoneAbbreviation()})`;

export const hourOffsetFromUTC = (timeZone: string) => {
  const formatForTimezone = Intl.DateTimeFormat(navigator.language, {
    timeZone,
    timeZoneName: 'shortOffset',
  });
  const offset = formatForTimezone
    .formatToParts(new Date())
    .find((part) => part.type === 'timeZoneName')?.value;

  const withoutGMT = offset?.replace('GMT', '');
  if (!withoutGMT) {
    return 0;
  }

  const [hours = '0', minutes = '0'] = withoutGMT.split(':');
  const parsedHours = parseInt(hours, 10);
  const parsedMinutes = (parseInt(minutes, 10) / 60) * (parsedHours < 0 ? -1 : 1);
  return parsedHours + parsedMinutes;
};

import cronstrue from 'cronstrue';

export const humanCronString = (cronSchedule: string) => {
  const standardCronString = convertIfSpecial(cronSchedule);
  try {
    return cronstrue.toString(standardCronString);
  } catch {
    return 'Invalid cron string';
  }
};

// https://en.wikipedia.org/wiki/Cron#Nonstandard_predefined_scheduling_definitions
const convertIfSpecial = (maybeSpecial: string) => {
  switch (maybeSpecial) {
    case '@yearly':
    case '@annually':
      return '0 0 1 1 *';
    case '@monthly':
      return '0 0 1 * *';
    case '@weekly':
      return '0 0 * * 0';
    case '@daily':
    case '@midnight':
      return '0 0 * * *';
    case '@hourly':
      return '0 * * * *';
    default:
      return maybeSpecial;
  }
};

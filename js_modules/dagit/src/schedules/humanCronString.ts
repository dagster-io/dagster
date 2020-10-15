import cronstrue from 'cronstrue';

export const humanCronString = (cronSchedule: string) => {
  try {
    return cronstrue.toString(cronSchedule);
  } catch {
    return 'Invalid cron string';
  }
};

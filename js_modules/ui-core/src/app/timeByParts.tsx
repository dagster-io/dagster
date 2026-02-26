export const timeByParts = (msec: number) => {
  let count = Math.abs(msec);

  const milliseconds = count % 1000;
  count = (count - milliseconds) / 1000;

  const seconds = count % 60;
  count = (count - seconds) / 60;

  const minutes = count % 60;
  count = (count - minutes) / 60;

  const hours = count;

  return {hours, minutes, seconds, milliseconds};
};

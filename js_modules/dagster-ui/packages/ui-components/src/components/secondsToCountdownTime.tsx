const ONE_HOUR_SEC = 3600;
const ONE_MINUTE_SEC = 60;

export const secondsToCountdownTime = (seconds: number) => {
  const hours = Math.floor(seconds / ONE_HOUR_SEC);
  const minutes = Math.floor((seconds % ONE_HOUR_SEC) / ONE_MINUTE_SEC);
  const sec = Math.round(seconds % ONE_MINUTE_SEC);

  const secondsString = sec < 10 ? `0${sec}` : `${sec}`;
  const minutesString = hours && minutes < 10 ? `0${minutes}` : `${minutes}`;
  const minutesAndSeconds = `${minutesString}:${secondsString}`;
  return hours ? `${hours}:${minutesAndSeconds}` : `${minutesAndSeconds}`;
};

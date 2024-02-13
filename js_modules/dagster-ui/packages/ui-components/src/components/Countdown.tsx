import * as React from 'react';

export type CountdownStatus = 'counting' | 'idle';

interface Config {
  duration: number;
  status: CountdownStatus;
  interval?: number;
  onComplete?: () => void;
}

/**
 * A hook that performs a countdown for a specified duration and interval.
 *
 * - duration
 *      The length of the countdown
 * - interval
 *      The interval at which the countdown will tick down
 * - onComplete
 *      A function to indicate when the countdown has reached zero, signaling to the
 *      parent that `status` may be updated
 * - status
 *      Whether the countdown should be in progress ("counting") or idle. An effect
 *      triggers the countdown to begin when this value changes to "counting".
 */
export const useCountdown = (config: Config) => {
  const {duration, interval = 1000, onComplete, status} = config;

  const [remainingTime, setRemainingTime] = React.useState<number>(duration);
  const token = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const clearToken = React.useCallback(() => {
    token.current && clearInterval(token.current);
    token.current = null;
  }, []);

  React.useEffect(() => {
    clearToken();
    if (status === 'counting') {
      setRemainingTime(duration);
      token.current = setInterval(() => {
        setRemainingTime((current) => Math.max(0, current - interval));
      }, interval);
    }

    return () => clearToken();
  }, [clearToken, duration, interval, status]);

  React.useEffect(() => {
    if (remainingTime === 0) {
      clearToken();
      onComplete && onComplete();
    }
  }, [clearToken, onComplete, remainingTime]);

  return remainingTime;
};

interface Props extends Config {
  message: (timeRemaining: number) => React.ReactNode;
}

export const Countdown = (props: Props) => {
  const {message, ...rest} = props;
  const remainingTime = useCountdown(rest);
  return <>{message(remainingTime)}</>;
};

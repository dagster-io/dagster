import {useDelayedState} from './useDelayedState';

interface Props {
  delayMsec?: number;
  children: React.ReactNode;
}

const DEFAULT_DELAY = 1000;

/**
 * While waiting for a delay to complete, show an empty span. This is useful for
 * delayed loading states, e.g. to avoid flashing a spinner during a fast loading period.
 */
export const Delayed = ({delayMsec = DEFAULT_DELAY, children}: Props) => {
  const ready = useDelayedState(delayMsec);
  return ready ? <>{children}</> : <span />;
};

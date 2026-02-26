import {useEffect, useReducer} from 'react';

export const LiveDuration = ({start, end}: {start: number; end?: number | null}) => {
  const [_, rerender] = useReducer((s: number, _: any) => s + 1, 0);
  useEffect(() => {
    if (end) {
      return;
    }
    const intervalId = setInterval(rerender, 1000);
    return () => clearInterval(intervalId);
  }, [start, end]);
  const duration = end ? end - start : Date.now() - start;

  return <span>{formatDuration(duration)}</span>;
};

const formatDuration = (duration: number) => {
  const seconds = Math.floor((duration / 1000) % 60);
  const minutes = Math.floor((duration / (1000 * 60)) % 60);
  const hours = Math.floor((duration / (1000 * 60 * 60)) % 24);
  const days = Math.floor(duration / (1000 * 60 * 60 * 24));

  let result = '';
  if (days > 0) {
    result += `${days}d `;
    result += `${hours}h`;
  } else if (hours > 0) {
    result += `${hours}h `;
    result += `${minutes}m`;
  } else if (minutes > 0) {
    result += `${minutes}m `;
    result += `${seconds}s`;
  } else if (seconds > 0) {
    result += `${seconds}s`;
  }
  return result.trim();
};

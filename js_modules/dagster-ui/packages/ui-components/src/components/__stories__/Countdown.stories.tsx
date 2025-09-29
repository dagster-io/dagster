import {useCallback, useState} from 'react';

import {Button} from '../Button';
import {Countdown, useCountdown} from '../Countdown';
import {Group} from '../Group';
import {secondsToCountdownTime} from '../secondsToCountdownTime';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useCountdown',
  component: Countdown,
};

export const FiveSeconds = () => {
  const [status, setStatus] = useState<'counting' | 'idle'>('idle');

  const onComplete = useCallback(() => setStatus('idle'), []);

  const timeRemaining = useCountdown({
    duration: 5000,
    onComplete,
    status,
  });

  const message = (timeRemaining: number) => {
    if (status === 'idle') {
      return <div>Waiting for refresh…</div>;
    }
    const seconds = Math.floor(timeRemaining / 1000);
    return <div>{`Refresh in ${secondsToCountdownTime(seconds)}`}</div>;
  };

  return (
    <Group direction="column" spacing={12}>
      <Group direction="row" spacing={8}>
        <Button onClick={() => setStatus('counting')}>Set counting</Button>
        <Button onClick={() => setStatus('idle')}>Set idle</Button>
      </Group>
      {message(timeRemaining)}
    </Group>
  );
};

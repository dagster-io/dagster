import {useState} from 'react';

import {Alert, AlertIntent} from '../Alert';
import {Box} from '../Box';
import {Button} from '../Button';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Alert',
  component: Alert,
};

const intents: AlertIntent[] = ['info', 'warning', 'error', 'success', 'none'];

export const Intents = () => {
  const [isClosed, updateClosed] = useState<boolean[]>(intents.map(() => false));
  const setClosed = (index: number, closed: boolean) => {
    const newClosed = Array.from(isClosed);
    newClosed[index] = closed;
    updateClosed(newClosed);
  };

  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {intents.map((intent) => (
        <Alert
          key={intent}
          intent={intent}
          title="This pipeline run is queued."
          description={
            <div>
              Click <a href="#">here</a> to proceed.
            </div>
          }
        />
      ))}
      {intents.map((intent, i) =>
        !isClosed[i] ? (
          <Alert
            key={`${intent}-closable`}
            intent={intent}
            title="You can dismiss me."
            description="This alert can be dismissed."
            onClose={() => setClosed(i, true)}
          />
        ) : null,
      )}
      {intents.map((intent, i) =>
        !isClosed[i] ? (
          <Alert
            key={`${intent}-custom-right-button`}
            intent={intent}
            title="You can take a CTA action on me."
            description="This alert has a button."
            rightButton={<Button onClick={() => setClosed(i, true)}>Go to Billing</Button>}
          />
        ) : null,
      )}
    </Box>
  );
};

import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Alert, AlertIntent} from './Alert';
import {Box} from './Box';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Alert',
  component: Alert,
} as Meta;

const intents: AlertIntent[] = ['info', 'warning', 'error', 'success'];

export const Intents = () => {
  const [isClosed, updateClosed] = React.useState<boolean[]>(intents.map(() => false));
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
    </Box>
  );
};

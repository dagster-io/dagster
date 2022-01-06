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
    </Box>
  );
};

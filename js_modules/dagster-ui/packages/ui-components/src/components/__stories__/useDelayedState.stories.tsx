import * as React from 'react';
import {Meta} from '@storybook/react';

import {Box} from '../Box';
import {Button} from '../Button';
import {useDelayedState} from '../useDelayedState';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useDelayedState',
} as Meta;

export const Default = () => {
  const notDisabled = useDelayedState(5000);
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <div>The button will become enabled after five seconds.</div>
      <div>
        <Button disabled={!notDisabled}>Wait for it</Button>
      </div>
    </Box>
  );
};

import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Box} from './Box';
import {Colors} from './Colors';
import {Group} from './Group';
import {ProgressBar} from './ProgressBar';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ProgressBar',
  component: ProgressBar,
} as Meta;

export const Sizes = () => {
  return (
    <Group direction="column" spacing={32}>
      <Box padding={20} border={{side: 'all', width: 1, color: Colors.Gray100}}>
        <Group direction="column" spacing={16}>
          <ProgressBar intent="primary" value={0.1} animate={true} />
          <ProgressBar intent="primary" value={0.7} />
        </Group>
      </Box>
      <Box padding={20} border={{side: 'all', width: 1, color: Colors.Gray100}}>
        <Group direction="column" spacing={16}>
          <ProgressBar intent="primary" value={0.1} animate={true} fillColor={Colors.Blue500} />
          <ProgressBar intent="primary" value={0.7} fillColor={Colors.Blue500} />
        </Group>
      </Box>
    </Group>
  );
};

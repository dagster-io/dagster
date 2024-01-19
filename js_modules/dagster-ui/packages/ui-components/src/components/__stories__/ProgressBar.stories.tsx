import {Meta} from '@storybook/react';
import * as React from 'react';

import {Box} from '../Box';
import {Colors} from '../Color';
import {Group} from '../Group';
import {ProgressBar} from '../ProgressBar';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ProgressBar',
  component: ProgressBar,
} as Meta;

export const Sizes = () => {
  return (
    <Group direction="column" spacing={32}>
      <Box padding={20} border="all">
        <Group direction="column" spacing={16}>
          <ProgressBar intent="primary" value={0.1} animate={true} />
          <ProgressBar intent="primary" value={0.7} />
        </Group>
      </Box>
      <Box padding={20} border="all">
        <Group direction="column" spacing={16}>
          <ProgressBar
            intent="primary"
            value={0.1}
            animate={true}
            fillColor={Colors.accentBlue()}
          />
          <ProgressBar intent="primary" value={0.7} fillColor={Colors.accentBlue()} />
        </Group>
      </Box>
    </Group>
  );
};

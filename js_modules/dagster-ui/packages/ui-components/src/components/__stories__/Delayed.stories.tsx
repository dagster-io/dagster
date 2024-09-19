import {Meta} from '@storybook/react';

import {Box} from '../Box';
import {Colors} from '../Color';
import {Delayed} from '../Delayed';
import {Heading} from '../Text';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Delayed',
  component: Delayed,
} as Meta;

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <div>Wait 5 seconds for content to appear:</div>
      <Delayed delayMsec={5000}>
        <Box background={Colors.accentBlue()} padding={20}>
          <Heading color={Colors.textDefault()}>Hello world!</Heading>
        </Box>
      </Delayed>
    </Box>
  );
};

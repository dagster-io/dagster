import * as React from 'react';
import {Meta} from '@storybook/react';

import {colorAccentBlue} from '../../theme/color';
import {Box} from '../Box';
import {Icon} from '../Icon';
import {Caption} from '../Text';
import {UnstyledButton} from '../UnstyledButton';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'UnstyledButton',
  component: UnstyledButton,
} as Meta;

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
      <UnstyledButton>No style here at all</UnstyledButton>
      <UnstyledButton>
        <Caption>Hey I am a Caption</Caption>
      </UnstyledButton>
      <UnstyledButton>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Icon name="account_tree" />
          <div>A button with icon and text</div>
        </Box>
      </UnstyledButton>
      <UnstyledButton disabled>Disabled button</UnstyledButton>
      <UnstyledButton>
        <span style={{color: colorAccentBlue()}}>Button with blue text</span>
      </UnstyledButton>
      <UnstyledButton disabled>
        <span style={{color: colorAccentBlue()}}>Disabled button with blue text</span>
      </UnstyledButton>
    </Box>
  );
};

export const UnstyledWithLargerClickArea = () => {
  return (
    <Box padding={24}>
      <UnstyledButton $expandedClickPx={24}>Lots more to click on</UnstyledButton>
    </Box>
  );
};

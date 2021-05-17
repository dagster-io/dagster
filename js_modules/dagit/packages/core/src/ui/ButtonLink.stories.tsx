import {Colors} from '@blueprintjs/core';
import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Box} from './Box';
import {ButtonLink} from './ButtonLink';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ButtonLink',
  component: ButtonLink,
} as Meta;

type Props = React.ComponentProps<typeof ButtonLink>;
const Template: Story<Props> = (props) => <ButtonLink {...props} />;

export const ColorString = Template.bind({});
ColorString.args = {
  children: 'Hello world',
  color: Colors.COBALT4,
};

export const ColorMap = Template.bind({});
ColorMap.args = {
  children: 'Hello world',
  color: {
    link: Colors.COBALT4,
    hover: Colors.COBALT1,
    active: Colors.ORANGE1,
  },
};

export const HoverUnderline = Template.bind({});
HoverUnderline.args = {
  children: 'Hello world',
  color: Colors.COBALT4,
  underline: 'hover',
};

export const WhiteLinkOnBlack = () => {
  return (
    <Box background={Colors.BLACK} padding={16}>
      <ButtonLink color={{link: Colors.WHITE, hover: Colors.LIGHT_GRAY1}} underline="always">
        Hello world
      </ButtonLink>
    </Box>
  );
};

export const WithinText = () => {
  return (
    <div>
      Lorem ipsum{' '}
      <ButtonLink color={{link: Colors.COBALT4, hover: Colors.BLUE1}} underline="always">
        dolor sit
      </ButtonLink>{' '}
      amet edipiscing.
    </div>
  );
};

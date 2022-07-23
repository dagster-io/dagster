import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Box} from './Box';
import {ButtonLink} from './ButtonLink';
import {Colors} from './Colors';

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
  color: Colors.Blue500,
};

export const ColorMap = Template.bind({});
ColorMap.args = {
  children: 'Hello world',
  color: {
    link: Colors.Blue500,
    hover: Colors.Blue700,
    active: Colors.Yellow700,
  },
};

export const HoverUnderline = Template.bind({});
HoverUnderline.args = {
  children: 'Hello world',
  color: Colors.Blue500,
  underline: 'hover',
};

export const WhiteLinkOnBlack = () => {
  return (
    <Box background={Colors.Dark} padding={16}>
      <ButtonLink color={{link: Colors.White, hover: Colors.Gray200}} underline="always">
        Hello world
      </ButtonLink>
    </Box>
  );
};

export const WithinText = () => {
  return (
    <div>
      Lorem ipsum{' '}
      <ButtonLink color={{link: Colors.Blue500, hover: Colors.Link}} underline="always">
        dolor sit
      </ButtonLink>{' '}
      amet edipiscing.
    </div>
  );
};

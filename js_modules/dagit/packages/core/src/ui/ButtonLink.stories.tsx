import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Box} from './Box';
import {ButtonLink} from './ButtonLink';
import {ColorsWIP} from './Colors';

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
  color: ColorsWIP.Blue500,
};

export const ColorMap = Template.bind({});
ColorMap.args = {
  children: 'Hello world',
  color: {
    link: ColorsWIP.Blue500,
    hover: ColorsWIP.Blue700,
    active: ColorsWIP.Yellow700,
  },
};

export const HoverUnderline = Template.bind({});
HoverUnderline.args = {
  children: 'Hello world',
  color: ColorsWIP.Blue500,
  underline: 'hover',
};

export const WhiteLinkOnBlack = () => {
  return (
    <Box background={ColorsWIP.Dark} padding={16}>
      <ButtonLink color={{link: ColorsWIP.White, hover: ColorsWIP.Gray200}} underline="always">
        Hello world
      </ButtonLink>
    </Box>
  );
};

export const WithinText = () => {
  return (
    <div>
      Lorem ipsum{' '}
      <ButtonLink color={{link: ColorsWIP.Blue500, hover: ColorsWIP.Link}} underline="always">
        dolor sit
      </ButtonLink>{' '}
      amet edipiscing.
    </div>
  );
};

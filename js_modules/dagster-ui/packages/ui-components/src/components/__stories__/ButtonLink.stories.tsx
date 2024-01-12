import {Story, Meta} from '@storybook/react';
import * as React from 'react';

import {ButtonLink} from '../ButtonLink';
import {Colors} from '../Color';

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
  color: Colors.linkDefault(),
};

export const ColorMap = Template.bind({});
ColorMap.args = {
  children: 'Hello world',
  color: {
    link: Colors.linkDefault(),
    hover: Colors.linkHover(),
    active: Colors.linkHover(),
  },
};

export const HoverUnderline = Template.bind({});
HoverUnderline.args = {
  children: 'Hello world',
  color: Colors.linkDefault(),
  underline: 'hover',
};

export const WithinText = () => {
  return (
    <div>
      Lorem ipsum{' '}
      <ButtonLink
        color={{link: Colors.linkDefault(), hover: Colors.linkHover()}}
        underline="always"
      >
        dolor sit
      </ButtonLink>{' '}
      amet edipiscing.
    </div>
  );
};

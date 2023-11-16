import {Story, Meta} from '@storybook/react';
import * as React from 'react';

import {colorLinkDefault, colorLinkHover} from '../../theme/color';
import {ButtonLink} from '../ButtonLink';

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
  color: colorLinkDefault(),
};

export const ColorMap = Template.bind({});
ColorMap.args = {
  children: 'Hello world',
  color: {
    link: colorLinkDefault(),
    hover: colorLinkHover(),
    active: colorLinkHover(),
  },
};

export const HoverUnderline = Template.bind({});
HoverUnderline.args = {
  children: 'Hello world',
  color: colorLinkDefault(),
  underline: 'hover',
};

export const WithinText = () => {
  return (
    <div>
      Lorem ipsum{' '}
      <ButtonLink color={{link: colorLinkDefault(), hover: colorLinkHover()}} underline="always">
        dolor sit
      </ButtonLink>{' '}
      amet edipiscing.
    </div>
  );
};

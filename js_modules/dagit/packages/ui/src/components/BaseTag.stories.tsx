import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {BaseTag} from './BaseTag';
import {Colors} from './Colors';
import {Group} from './Group';
import {Icon} from './Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'BaseTag',
  component: BaseTag,
} as Meta;

const COLORS = [
  {fillColor: Colors.Gray10, textColor: Colors.Gray900, iconColor: Colors.Gray900},
  {fillColor: Colors.Blue50, textColor: Colors.Blue700, iconColor: Colors.Blue500},
  {fillColor: Colors.Green50, textColor: Colors.Green700, iconColor: Colors.Green500},
  {fillColor: Colors.Yellow50, textColor: Colors.Yellow700, iconColor: Colors.Yellow500},
  {fillColor: Colors.Red50, textColor: Colors.Red700, iconColor: Colors.Red500},
  {fillColor: Colors.Olive50, textColor: Colors.Olive700, iconColor: Colors.Olive500},
];

export const Basic = () => {
  return (
    <Group direction="column" spacing={8}>
      {COLORS.map(({fillColor, textColor, iconColor}, ii) => (
        <Group direction="row" spacing={8} key={ii}>
          <BaseTag
            fillColor={fillColor}
            textColor={textColor}
            icon={<Icon name="info" color={iconColor} />}
          />
          <BaseTag
            fillColor={fillColor}
            textColor={textColor}
            icon={<Icon name="alternate_email" color={iconColor} />}
            label="Lorem"
          />
          <BaseTag
            fillColor={fillColor}
            textColor={textColor}
            rightIcon={<Icon name="toggle_off" color={iconColor} />}
            label="Lorem"
          />
          <BaseTag fillColor={fillColor} textColor={textColor} label="Lorem" />
        </Group>
      ))}
    </Group>
  );
};

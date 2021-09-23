import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {BaseTag} from './BaseTag';
import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconWIP} from './Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'BaseTag',
  component: BaseTag,
} as Meta;

const COLORS = [
  {fillColor: ColorsWIP.Gray10, textColor: ColorsWIP.Gray900, iconColor: ColorsWIP.Gray900},
  {fillColor: ColorsWIP.Blue50, textColor: ColorsWIP.Blue700, iconColor: ColorsWIP.Blue500},
  {fillColor: ColorsWIP.Green50, textColor: ColorsWIP.Green700, iconColor: ColorsWIP.Green500},
  {fillColor: ColorsWIP.Yellow50, textColor: ColorsWIP.Yellow700, iconColor: ColorsWIP.Yellow500},
  {fillColor: ColorsWIP.Red50, textColor: ColorsWIP.Red700, iconColor: ColorsWIP.Red500},
  {fillColor: ColorsWIP.Olive50, textColor: ColorsWIP.Olive700, iconColor: ColorsWIP.Olive500},
];

export const Basic = () => {
  return (
    <Group direction="column" spacing={8}>
      {COLORS.map(({fillColor, textColor, iconColor}, ii) => (
        <Group direction="row" spacing={8} key={ii}>
          <BaseTag
            fillColor={fillColor}
            textColor={textColor}
            icon={<IconWIP name="info" color={iconColor} />}
          />
          <BaseTag
            fillColor={fillColor}
            textColor={textColor}
            icon={<IconWIP name="alternate_email" color={iconColor} />}
            label="Lorem"
          />
          <BaseTag
            fillColor={fillColor}
            textColor={textColor}
            rightIcon={<IconWIP name="toggle_off" color={iconColor} />}
            label="Lorem"
          />
          <BaseTag fillColor={fillColor} textColor={textColor} label="Lorem" />
        </Group>
      ))}
    </Group>
  );
};

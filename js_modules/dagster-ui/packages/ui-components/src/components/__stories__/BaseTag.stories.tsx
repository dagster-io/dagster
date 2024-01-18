import * as React from 'react';
import {Meta} from '@storybook/react';

import {
  colorAccentBlue,
  colorAccentCyan,
  colorAccentGray,
  colorAccentGreen,
  colorAccentLime,
  colorAccentRed,
  colorAccentYellow,
  colorBackgroundBlue,
  colorBackgroundCyan,
  colorBackgroundGray,
  colorBackgroundGreen,
  colorBackgroundLime,
  colorBackgroundRed,
  colorBackgroundYellow,
  colorTextCyan,
  colorTextDefault,
} from '../../theme/color';
import {BaseTag} from '../BaseTag';
import {Group} from '../Group';
import {Icon} from '../Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'BaseTag',
  component: BaseTag,
} as Meta;

const COLORS = [
  {fillColor: colorBackgroundGray(), textColor: colorTextDefault(), iconColor: colorAccentGray()},
  {fillColor: colorBackgroundBlue(), textColor: colorAccentBlue(), iconColor: colorAccentBlue()},
  {fillColor: colorBackgroundCyan(), textColor: colorTextCyan(), iconColor: colorAccentCyan()},
  {fillColor: colorBackgroundGreen(), textColor: colorAccentGreen(), iconColor: colorAccentGreen()},
  {fillColor: colorBackgroundLime(), textColor: colorAccentLime(), iconColor: colorAccentLime()},
  {
    fillColor: colorBackgroundYellow(),
    textColor: colorAccentYellow(),
    iconColor: colorAccentYellow(),
  },
  {fillColor: colorBackgroundRed(), textColor: colorAccentRed(), iconColor: colorAccentRed()},
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

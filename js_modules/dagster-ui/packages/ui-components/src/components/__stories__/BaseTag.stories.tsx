import {Meta} from '@storybook/react';

import {BaseTag} from '../BaseTag';
import {Colors} from '../Color';
import {Group} from '../Group';
import {Icon} from '../Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'BaseTag',
  component: BaseTag,
} as Meta;

const COLORS = [
  {
    fillColor: Colors.backgroundGray(),
    textColor: Colors.textDefault(),
    iconColor: Colors.accentGray(),
  },
  {
    fillColor: Colors.backgroundBlue(),
    textColor: Colors.accentBlue(),
    iconColor: Colors.accentBlue(),
  },
  {
    fillColor: Colors.backgroundCyan(),
    textColor: Colors.textCyan(),
    iconColor: Colors.accentCyan(),
  },
  {
    fillColor: Colors.backgroundGreen(),
    textColor: Colors.accentGreen(),
    iconColor: Colors.accentGreen(),
  },
  {
    fillColor: Colors.backgroundLime(),
    textColor: Colors.accentLime(),
    iconColor: Colors.accentLime(),
  },
  {
    fillColor: Colors.backgroundYellow(),
    textColor: Colors.accentYellow(),
    iconColor: Colors.accentYellow(),
  },
  {fillColor: Colors.backgroundRed(), textColor: Colors.accentRed(), iconColor: Colors.accentRed()},
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

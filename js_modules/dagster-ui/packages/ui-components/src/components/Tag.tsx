// eslint-disable-next-line no-restricted-imports
import * as React from 'react';
import {Tag as BlueprintTag} from '@blueprintjs/core';

import {
  colorAccentBlue,
  colorAccentGray,
  colorAccentGreen,
  colorAccentRed,
  colorAccentYellow,
  colorBackgroundBlue,
  colorBackgroundGray,
  colorBackgroundGreen,
  colorBackgroundRed,
  colorBackgroundYellow,
  colorTextBlue,
  colorTextDefault,
  colorTextGreen,
  colorTextRed,
  colorTextYellow,
} from '../theme/color';
import {BaseTag} from './BaseTag';
import {Icon, IconName} from './Icon';
import {Spinner} from './Spinner';

const intentToFillColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return colorBackgroundBlue();
    case 'danger':
      return colorBackgroundRed();
    case 'success':
      return colorBackgroundGreen();
    case 'warning':
      return colorBackgroundYellow();
    case 'none':
    default:
      return colorBackgroundGray();
  }
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return colorTextBlue();
    case 'danger':
      return colorTextRed();
    case 'success':
      return colorTextGreen();
    case 'warning':
      return colorTextYellow();
    case 'none':
    default:
      return colorTextDefault();
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return colorAccentBlue();
    case 'danger':
      return colorAccentRed();
    case 'success':
      return colorAccentGreen();
    case 'warning':
      return colorAccentYellow();
    case 'none':
    default:
      return colorAccentGray();
  }
};

interface Props extends Omit<React.ComponentProps<typeof BlueprintTag>, 'icon' | 'rightIcon'> {
  children?: React.ReactNode;
  icon?: IconName | 'spinner';
  rightIcon?: IconName | 'spinner';
  tooltipText?: string;
}

interface IconOrSpinnerProps {
  icon: IconName | 'spinner' | null;
  color: string;
}

const IconOrSpinner = React.memo(({icon, color}: IconOrSpinnerProps) => {
  if (icon === 'spinner') {
    return <Spinner fillColor={color} purpose="body-text" />;
  }
  return icon ? <Icon name={icon} color={color} /> : null;
});

export const Tag = (props: Props) => {
  const {children, icon = null, rightIcon = null, intent, ...rest} = props;

  const fillColor = intentToFillColor(intent);
  const textColor = intentToTextColor(intent);
  const iconColor = intentToIconColor(intent);

  return (
    <BaseTag
      {...rest}
      fillColor={fillColor}
      textColor={textColor}
      icon={<IconOrSpinner icon={icon} color={iconColor} />}
      rightIcon={<IconOrSpinner icon={rightIcon} color={iconColor} />}
      label={children}
    />
  );
};

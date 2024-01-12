// eslint-disable-next-line no-restricted-imports
import {Tag as BlueprintTag} from '@blueprintjs/core';
import * as React from 'react';

import {BaseTag} from './BaseTag';
import {Colors} from './Color';
import {IconName, Icon} from './Icon';
import {Spinner} from './Spinner';

const intentToFillColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.backgroundBlue();
    case 'danger':
      return Colors.backgroundRed();
    case 'success':
      return Colors.backgroundGreen();
    case 'warning':
      return Colors.backgroundYellow();
    case 'none':
    default:
      return Colors.backgroundGray();
  }
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.textBlue();
    case 'danger':
      return Colors.textRed();
    case 'success':
      return Colors.textGreen();
    case 'warning':
      return Colors.textYellow();
    case 'none':
    default:
      return Colors.textDefault();
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.accentBlue();
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'none':
    default:
      return Colors.accentGray();
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

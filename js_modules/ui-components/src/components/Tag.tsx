import {ReactNode, memo} from 'react';

import {BaseTag, BaseTagProps} from './BaseTag';
import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import {Intent} from './Intent';
import {Spinner} from './Spinner';

const intentToFillColor = (intent: Intent) => {
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

const intentToTextColor = (intent: Intent) => {
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

const intentToIconColor = (intent: Intent) => {
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

interface IconOrSpinnerProps {
  icon: IconName | 'spinner' | null;
  color: string;
}

const IconOrSpinner = memo(({icon, color}: IconOrSpinnerProps) => {
  if (icon === 'spinner') {
    return <Spinner fillColor={color} purpose="body-text" />;
  }
  return icon ? <Icon name={icon} color={color} /> : null;
});

IconOrSpinner.displayName = 'IconOrSpinner';

interface Props extends Omit<BaseTagProps, 'label' | 'icon' | 'rightIcon'> {
  children?: ReactNode;
  intent?: Intent;
  icon?: IconName | 'spinner';
  rightIcon?: IconName | 'spinner';
  tooltipText?: string;
  disabled?: boolean;
}

export const Tag = (props: Props) => {
  const {children, icon = null, rightIcon = null, intent = 'none', ...rest} = props;

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

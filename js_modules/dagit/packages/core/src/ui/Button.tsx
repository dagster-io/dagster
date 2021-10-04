// eslint-disable-next-line no-restricted-imports
import {Button as BlueprintButton} from '@blueprintjs/core';
import * as React from 'react';

import {BaseButton} from './BaseButton';
import {ColorsWIP} from './Colors';
import {Spinner} from './Spinner';

type BlueprintIntent = React.ComponentProps<typeof BlueprintButton>['intent'];
type BlueprintOutlined = React.ComponentProps<typeof BlueprintButton>['outlined'];

const intentToFillColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    return 'transparent';
  }
  switch (intent) {
    case 'primary':
      return ColorsWIP.Gray900;
    case 'danger':
      return ColorsWIP.Red500;
    case 'success':
      return ColorsWIP.Green500;
    case 'warning':
      return ColorsWIP.Yellow500;
    case 'none':
    default:
      return 'transparent';
  }
};

const intentToTextColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    switch (intent) {
      case 'primary':
        return ColorsWIP.Gray900;
      case 'danger':
        return ColorsWIP.Red500;
      case 'success':
        return ColorsWIP.Green500;
      case 'warning':
        return ColorsWIP.Yellow500;
      case 'none':
      default:
        return ColorsWIP.Dark;
    }
  }
  return !intent || intent === 'none' ? ColorsWIP.Dark : ColorsWIP.White;
};

const intentToStrokeColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (!intent || intent === 'none' || outlined) {
    switch (intent) {
      case 'primary':
        return ColorsWIP.Gray900;
      case 'danger':
        return ColorsWIP.Red500;
      case 'success':
        return ColorsWIP.Green500;
      case 'warning':
        return ColorsWIP.Yellow500;
      case 'none':
      default:
        return ColorsWIP.Gray300;
    }
  }
  return 'transparent';
};

const intentToSpinnerColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    switch (intent) {
      case 'primary':
        return ColorsWIP.Gray600;
      case 'danger':
        return ColorsWIP.Red500;
      case 'success':
        return ColorsWIP.Green500;
      case 'warning':
        return ColorsWIP.Yellow500;
      case 'none':
      default:
        return ColorsWIP.Gray600;
    }
  }
  return !intent || intent === 'none' ? ColorsWIP.Gray600 : ColorsWIP.White;
};

export const ButtonWIP = React.forwardRef(
  (
    props: React.ComponentProps<typeof BlueprintButton>,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const {children, icon, intent, loading, outlined, rightIcon, ...rest} = props;

    const fillColor = intentToFillColor(intent, outlined);
    const textColor = intentToTextColor(intent, outlined);
    const strokeColor = intentToStrokeColor(intent, outlined);

    let iconOrSpinner = icon;
    let rightIconOrSpinner = rightIcon;

    if (loading) {
      const spinnerColor = intentToSpinnerColor(intent, outlined);
      iconOrSpinner = icon ? <Spinner purpose="body-text" fillColor={spinnerColor} /> : icon;
      rightIconOrSpinner =
        rightIcon && !icon ? <Spinner purpose="body-text" fillColor={spinnerColor} /> : rightIcon;
    }

    return (
      <BaseButton
        {...rest}
        icon={iconOrSpinner}
        rightIcon={rightIconOrSpinner}
        loading={loading}
        fillColor={fillColor}
        textColor={textColor}
        strokeColor={strokeColor}
        label={children}
        ref={ref}
      />
    );
  },
);

ButtonWIP.displayName = 'Button';

import {Button as BlueprintButton} from '@blueprintjs/core';
import * as React from 'react';

import {BaseButton} from './BaseButton';
import {ColorsWIP} from './Colors';
import {Spinner} from './Spinner';

const intentToFillColor = (intent: React.ComponentProps<typeof BlueprintButton>['intent']) => {
  switch (intent) {
    case 'primary':
      return ColorsWIP.Gray800;
    case 'danger':
      return ColorsWIP.Red700;
    case 'success':
      return ColorsWIP.Green700;
    case 'warning':
      return ColorsWIP.Yellow700;
    case 'none':
    default:
      return 'transparent';
  }
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintButton>['intent']) => {
  switch (intent) {
    case 'primary':
    case 'danger':
    case 'success':
    case 'warning':
      return ColorsWIP.White;
    case 'none':
    default:
      return ColorsWIP.Dark;
  }
};

const intentToSpinnerColor = (intent: React.ComponentProps<typeof BlueprintButton>['intent']) => {
  switch (intent) {
    case 'primary':
    case 'danger':
    case 'success':
    case 'warning':
      return ColorsWIP.White;
    case 'none':
    default:
      return ColorsWIP.Gray600;
  }
};

export const ButtonWIP = React.forwardRef(
  (
    props: React.ComponentProps<typeof BlueprintButton>,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const {children, icon, intent, loading, rightIcon, ...rest} = props;

    const fillColor = intentToFillColor(intent);
    const textColor = intentToTextColor(intent);

    let iconOrSpinner = icon;
    let rightIconOrSpinner = rightIcon;

    if (loading) {
      const spinnerColor = intentToSpinnerColor(intent);
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
        stroke={!intent || intent === 'none'}
        label={children}
        ref={ref}
      />
    );
  },
);

ButtonWIP.displayName = 'Button';

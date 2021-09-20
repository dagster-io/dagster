import {Button as BlueprintButton} from '@blueprintjs/core';
import * as React from 'react';

import {BaseButton} from './BaseButton';
import {ColorsWIP} from './Colors';

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

export const ButtonWIP = React.forwardRef(
  (
    props: React.ComponentProps<typeof BlueprintButton>,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const {children, intent, ...rest} = props;

    const fillColor = intentToFillColor(intent);
    const textColor = intentToTextColor(intent);

    return (
      <BaseButton
        {...rest}
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

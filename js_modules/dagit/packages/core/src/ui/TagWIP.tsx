import {Tag as BlueprintTag} from '@blueprintjs/core';
import * as React from 'react';

import {BaseTag} from './BaseTag';
import {ColorsWIP} from './Colors';

const intentToFillColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return ColorsWIP.Blue50;
    case 'danger':
      return ColorsWIP.Red50;
    case 'success':
      return ColorsWIP.Green50;
    case 'warning':
      return ColorsWIP.Yellow50;
    case 'none':
    default:
      return ColorsWIP.Gray50;
  }
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return ColorsWIP.Blue700;
    case 'danger':
      return ColorsWIP.Red700;
    case 'success':
      return ColorsWIP.Green700;
    case 'warning':
      return ColorsWIP.Yellow700;
    case 'none':
    default:
      return ColorsWIP.Gray900;
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof BlueprintTag>['intent']) => {
  switch (intent) {
    case 'primary':
      return ColorsWIP.Blue500;
    case 'danger':
      return ColorsWIP.Red500;
    case 'success':
      return ColorsWIP.Green500;
    case 'warning':
      return ColorsWIP.Yellow500;
    case 'none':
    default:
      return ColorsWIP.Gray900;
  }
};

export const TagWIP = (props: React.ComponentProps<typeof BlueprintTag>) => {
  const {children, intent, ...rest} = props;

  const fillColor = intentToFillColor(intent);
  const textColor = intentToTextColor(intent);
  const iconColor = intentToIconColor(intent);

  return (
    <BaseTag
      {...rest}
      fillColor={fillColor}
      textColor={textColor}
      iconColor={iconColor}
      label={children}
    />
  );
};

TagWIP.displayName = 'Tag';

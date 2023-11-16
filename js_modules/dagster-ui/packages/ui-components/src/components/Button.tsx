// eslint-disable-next-line no-restricted-imports
import {AnchorButton as BlueprintAnchorButton, Button as BlueprintButton} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {CoreColors} from '../palettes/Colors';
import {
  colorAccentGray,
  colorAccentGreen,
  colorAccentPrimary,
  colorAccentRed,
  colorAccentReversed,
  colorAccentYellow,
  colorBorderDefault,
  colorTextDefault,
  colorTextGreen,
  colorTextRed,
  colorTextYellow,
} from '../theme/color';

import {BaseButton} from './BaseButton';
import {Spinner} from './Spinner';
import {StyledButton, StyledButtonText} from './StyledButton';

type BlueprintIntent = React.ComponentProps<typeof BlueprintButton>['intent'];
type BlueprintOutlined = React.ComponentProps<typeof BlueprintButton>['outlined'];

export const intentToFillColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    return 'transparent';
  }

  switch (intent) {
    case 'primary':
      return colorAccentPrimary();
    case 'danger':
      return colorAccentRed();
    case 'success':
      return colorAccentGreen();
    case 'warning':
      return colorAccentYellow();
    case 'none':
    default:
      return 'transparent';
  }
};

export const intentToTextColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (!outlined) {
    if (!intent || intent === 'none') {
      return colorAccentPrimary();
    }
    if (intent === 'primary') {
      return colorAccentReversed();
    }
    return CoreColors.White;
  }

  switch (intent) {
    case 'primary':
      return colorAccentPrimary();
    case 'danger':
      return colorTextRed();
    case 'success':
      return colorTextGreen();
    case 'warning':
      return colorTextYellow();
    case 'none':
    default:
      return colorAccentPrimary();
  }
};

export const intentToIconColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (!outlined) {
    if (!intent || intent === 'none') {
      return colorAccentPrimary();
    }
    if (intent === 'primary') {
      return colorAccentReversed();
    }
    return CoreColors.White;
  }

  switch (intent) {
    case 'primary':
      return colorAccentPrimary();
    case 'danger':
      return colorAccentRed();
    case 'success':
      return colorAccentGreen();
    case 'warning':
      return colorAccentYellow();
    case 'none':
    default:
      return colorAccentPrimary();
  }
};

export const intentToStrokeColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    switch (intent) {
      case 'primary':
        return colorBorderDefault();
      case 'danger':
        return colorAccentRed();
      case 'success':
        return colorAccentGreen();
      case 'warning':
        return colorAccentYellow();
      case 'none':
      default:
        return colorBorderDefault();
    }
  }

  return intent === undefined ? colorBorderDefault() : 'transparent';
};

export const intentToSpinnerColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    switch (intent) {
      case 'primary':
        return colorAccentGray();
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
  }
  return colorTextDefault();
};

export const Button = React.forwardRef(
  (
    props: React.ComponentProps<typeof BlueprintButton>,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const {children, icon, intent, loading, outlined, rightIcon, ...rest} = props;

    let iconOrSpinner = icon;

    if (loading) {
      const spinnerColor = intentToSpinnerColor(intent, outlined);
      iconOrSpinner = <Spinner purpose="body-text" fillColor={spinnerColor} />;
    }

    return (
      <BaseButton
        {...rest}
        icon={iconOrSpinner}
        rightIcon={rightIcon}
        loading={loading}
        fillColor={intentToFillColor(intent, outlined)}
        textColor={intentToTextColor(intent, outlined)}
        iconColor={intentToIconColor(intent, outlined)}
        strokeColor={intentToStrokeColor(intent, outlined)}
        label={children}
        ref={ref}
      />
    );
  },
);

Button.displayName = 'Button';

export const JoinedButtons = styled.div`
  display: flex;
  align-items: center;

  ${StyledButton}:not(:last-child),
  & > *:not(:last-child) ${StyledButton} {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
  }

  ${StyledButton}:not(:first-child),
  & > *:not(:first-child) ${StyledButton} {
    margin-left: -1px;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
  }
`;

export const ExternalAnchorButton = React.forwardRef(
  (
    props: Omit<React.ComponentProps<typeof BlueprintAnchorButton>, 'loading'>,
    ref: React.ForwardedRef<HTMLAnchorElement>,
  ) => {
    const {children, icon, intent, outlined, rightIcon, ...rest} = props;
    return (
      <StyledButton
        {...rest}
        as="a"
        target="_blank"
        rel="noreferrer nofollow"
        $fillColor={intentToFillColor(intent, outlined)}
        $strokeColor={intentToStrokeColor(intent, outlined)}
        $textColor={intentToTextColor(intent, outlined)}
        $iconColor={intentToIconColor(intent, outlined)}
        ref={ref}
      >
        {icon || null}
        {children ? <StyledButtonText>{children}</StyledButtonText> : null}
        {rightIcon || null}
      </StyledButton>
    );
  },
);

ExternalAnchorButton.displayName = 'ExternalAnchorButton';

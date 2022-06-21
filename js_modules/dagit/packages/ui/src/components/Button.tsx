// eslint-disable-next-line no-restricted-imports
import {AnchorButton as BlueprintAnchorButton, Button as BlueprintButton} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {BaseButton} from './BaseButton';
import {Colors} from './Colors';
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
      return Colors.Gray900;
    case 'danger':
      return Colors.Red500;
    case 'success':
      return Colors.Green500;
    case 'warning':
      return Colors.Yellow500;
    case 'none':
      return Colors.White;
    default:
      return 'transparent';
  }
};

export const intentToTextColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    switch (intent) {
      case 'primary':
        return Colors.Gray900;
      case 'danger':
        return Colors.Red500;
      case 'success':
        return Colors.Green500;
      case 'warning':
        return Colors.Yellow500;
      case 'none':
      default:
        return Colors.Dark;
    }
  }
  return !intent || intent === 'none' ? Colors.Dark : Colors.White;
};

export const intentToStrokeColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (!intent || intent === 'none' || outlined) {
    switch (intent) {
      case 'primary':
        return Colors.Gray900;
      case 'danger':
        return Colors.Red500;
      case 'success':
        return Colors.Green500;
      case 'warning':
        return Colors.Yellow500;
      case 'none':
      default:
        return Colors.Gray300;
    }
  }
  return 'transparent';
};

export const intentToSpinnerColor = (intent: BlueprintIntent, outlined: BlueprintOutlined) => {
  if (outlined) {
    switch (intent) {
      case 'primary':
        return Colors.Gray600;
      case 'danger':
        return Colors.Red500;
      case 'success':
        return Colors.Green500;
      case 'warning':
        return Colors.Yellow500;
      case 'none':
      default:
        return Colors.Gray600;
    }
  }
  return !intent || intent === 'none' ? Colors.Gray600 : Colors.White;
};

export const Button = React.forwardRef(
  (
    props: React.ComponentProps<typeof BlueprintButton>,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const {children, icon, intent, loading, outlined, rightIcon, ...rest} = props;

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
        fillColor={intentToFillColor(intent, outlined)}
        textColor={intentToTextColor(intent, outlined)}
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
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    margin-left: 1px;
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

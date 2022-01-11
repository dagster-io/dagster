// eslint-disable-next-line no-restricted-imports
import {Button as BlueprintButton, AnchorButton as BlueprintAnchorButton} from '@blueprintjs/core';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';

import {BaseButton} from './BaseButton';
import {ColorsWIP} from './Colors';
import {Spinner} from './Spinner';
import {StyledButton} from './StyledButton';

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
      return ColorsWIP.White;
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

ButtonWIP.displayName = 'Button';

interface AnchorButtonProps
  extends Omit<React.ComponentProps<typeof BlueprintAnchorButton>, 'loading' | 'onClick' | 'type'>,
    LinkProps {
  label?: React.ReactNode;
}

export const AnchorButton = React.forwardRef(
  (props: AnchorButtonProps, ref: React.ForwardedRef<HTMLAnchorElement>) => {
    const {children, icon, intent, outlined, rightIcon, ...rest} = props;
    return (
      <StyledButton
        {...rest}
        as={Link}
        $fillColor={intentToFillColor(intent, outlined)}
        $strokeColor={intentToStrokeColor(intent, outlined)}
        $textColor={intentToTextColor(intent, outlined)}
        ref={ref}
      >
        {icon || null}
        {children ? <span>{children}</span> : null}
        {rightIcon || null}
      </StyledButton>
    );
  },
);

AnchorButton.displayName = 'AnchorButton';

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
        {children ? <span>{children}</span> : null}
        {rightIcon || null}
      </StyledButton>
    );
  },
);

ExternalAnchorButton.displayName = 'ExternalAnchorButton';

import * as React from 'react';
import styled from 'styled-components';

import {BaseButton, BaseButtonProps, CommonButtonProps} from './BaseButton';
import {Colors} from './Color';
import {Intent} from './Intent';
import {Spinner} from './Spinner';
import {StyledButton, StyledButtonText} from './StyledButton';

// Outlined buttons

export const outlinedIntentToFillColor = () => {
  return 'transparent';
};

export const outlinedIntentToFillColorHover = (intent?: Intent) => {
  switch (intent) {
    case 'danger':
      return Colors.backgroundRed();
    case 'success':
      return Colors.backgroundGreen();
    case 'warning':
      return Colors.backgroundYellow();
    case 'primary':
    case 'none':
    default:
      return Colors.backgroundGray();
  }
};

export const outlinedIntentToStrokeColor = (intent?: Intent) => {
  switch (intent) {
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'none':
      return 'transparent';
    case 'primary':
    default:
      return Colors.borderDefault();
  }
};

export const outlinedIntentToStrokeColorHover = (intent?: Intent) => {
  switch (intent) {
    case 'danger':
      return Colors.accentRedHover();
    case 'success':
      return Colors.accentGreenHover();
    case 'warning':
      return Colors.accentYellowHover();
    case 'none':
      return 'transparent';
    case 'primary':
    default:
      return Colors.borderHover();
  }
};

export const outlinedIntentToTextColor = (intent?: Intent) => {
  switch (intent) {
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'primary':
    case 'none':
    default:
      return Colors.accentPrimary();
  }
};

export const outlinedIntentToIconColor = (intent?: Intent) => {
  switch (intent) {
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'primary':
    case 'none':
    default:
      return Colors.accentPrimary();
  }
};

export const outlinedIntentToSpinnerColor = (intent?: Intent) => {
  switch (intent) {
    case 'primary':
      return Colors.borderDefault();
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'primary':
    case 'none':
    default:
      return Colors.accentGray();
  }
};

// Filled buttons

export const intentToStrokeColor = (intent?: Intent) => {
  if (intent === undefined) {
    return Colors.borderDefault();
  }
  return 'transparent';
};

export const intentToFillColor = (intent?: Intent) => {
  switch (intent) {
    case 'primary':
      return Colors.accentPrimary();
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'none':
    default:
      return 'transparent';
  }
};

export const intentToFillColorHover = (intent?: Intent) => {
  switch (intent) {
    case 'primary':
      return Colors.accentPrimaryHover();
    case 'danger':
      return Colors.accentRedHover();
    case 'success':
      return Colors.accentGreenHover();
    case 'warning':
      return Colors.accentYellowHover();
    case 'none':
    default:
      return Colors.backgroundLightHover();
  }
};

export const intentToTextAndIconColor = (intent?: Intent) => {
  if (!intent || intent === 'none') {
    return Colors.accentPrimary();
  }
  if (intent === 'primary') {
    return Colors.accentReversed();
  }
  return Colors.alwaysWhite();
};

export const buildColorSet = (config: {intent?: Intent; outlined?: boolean}) => {
  const {intent, outlined} = config;
  const fillColor = outlined ? outlinedIntentToFillColor() : intentToFillColor(intent);
  const fillColorHover = outlined
    ? outlinedIntentToFillColorHover(intent)
    : intentToFillColorHover(intent);
  const textColor = outlined ? outlinedIntentToTextColor(intent) : intentToTextAndIconColor(intent);
  const iconColor = outlined ? outlinedIntentToIconColor(intent) : intentToTextAndIconColor(intent);
  const strokeColor = outlined ? outlinedIntentToStrokeColor(intent) : intentToStrokeColor(intent);
  const strokeColorHover = outlined
    ? outlinedIntentToStrokeColorHover(intent)
    : intentToStrokeColor(intent);

  return {
    fillColor,
    fillColorHover,
    textColor,
    iconColor,
    strokeColor,
    strokeColorHover,
  };
};

type ButtonProps = BaseButtonProps & {
  intent?: Intent;
  outlined?: boolean;
};

export const Button = React.forwardRef(
  (props: ButtonProps, ref: React.ForwardedRef<HTMLButtonElement>) => {
    const {children, icon, intent, loading, outlined, rightIcon, ...rest} = props;

    let iconOrSpinner = icon;

    if (loading) {
      const spinnerColor = outlined
        ? outlinedIntentToSpinnerColor(intent)
        : intentToTextAndIconColor(intent);
      iconOrSpinner = <Spinner purpose="body-text" fillColor={spinnerColor} />;
    }

    const {fillColor, fillColorHover, textColor, iconColor, strokeColor, strokeColorHover} =
      React.useMemo(() => buildColorSet({intent, outlined}), [intent, outlined]);

    return (
      <BaseButton
        {...rest}
        icon={iconOrSpinner}
        rightIcon={rightIcon}
        loading={loading}
        fillColor={fillColor}
        fillColorHover={fillColorHover}
        textColor={textColor}
        iconColor={iconColor}
        strokeColor={strokeColor}
        strokeColorHover={strokeColorHover}
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

  ${StyledButton}:focus-visible {
    z-index: 1;
    position: relative;
  }
`;

export type ExternalAnchorButtonProps = CommonButtonProps &
  React.ComponentPropsWithRef<'a'> & {
    intent?: Intent;
    outlined?: boolean;
  };

export const ExternalAnchorButton = React.forwardRef(
  (props: ExternalAnchorButtonProps, ref: React.ForwardedRef<HTMLAnchorElement>) => {
    const {children, icon, intent, outlined, rightIcon, ...rest} = props;

    const {fillColor, fillColorHover, textColor, iconColor, strokeColor, strokeColorHover} =
      React.useMemo(() => buildColorSet({intent, outlined}), [intent, outlined]);

    return (
      <StyledButton
        {...rest}
        as="a"
        target="_blank"
        rel="noreferrer nofollow"
        $fillColor={fillColor}
        $fillColorHover={fillColorHover}
        $strokeColor={strokeColor}
        $strokeColorHover={strokeColorHover}
        $textColor={textColor}
        $iconColor={iconColor}
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

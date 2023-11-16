import * as React from 'react';

import {
  colorAccentGray,
  colorAccentReversed,
  colorBackgroundDefault,
  colorTextDefault,
} from '../theme/color';

import {StyledButton, StyledButtonText} from './StyledButton';

interface CommonButtonProps {
  icon?: React.ReactNode;
  label?: React.ReactNode;
  loading?: boolean;
  rightIcon?: React.ReactNode;
  iconColor?: string;
  fillColor?: string;
  strokeColor?: string;
  textColor?: string;
}

interface BaseButtonProps extends CommonButtonProps, React.ComponentPropsWithRef<'button'> {}

export const BaseButton = React.forwardRef(
  (props: BaseButtonProps, ref: React.ForwardedRef<HTMLButtonElement>) => {
    const {
      fillColor = colorBackgroundDefault(),
      disabled,
      icon,
      label,
      loading,
      rightIcon,
      iconColor = colorAccentReversed(),
      textColor = colorTextDefault(),
      strokeColor = colorAccentGray(),
      ...rest
    } = props;

    return (
      <StyledButton
        {...rest}
        as="button"
        disabled={!!(disabled || loading)}
        $iconColor={iconColor}
        $fillColor={fillColor}
        $strokeColor={strokeColor}
        $textColor={textColor}
        ref={ref}
      >
        {icon || null}
        {label ? <StyledButtonText>{label}</StyledButtonText> : null}
        {rightIcon || null}
      </StyledButton>
    );
  },
);

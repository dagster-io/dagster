import * as React from 'react';

import {Colors} from './Color';
import {StyledButton, StyledButtonText} from './StyledButton';

interface CommonButtonProps {
  icon?: React.ReactNode;
  label?: React.ReactNode;
  loading?: boolean;
  rightIcon?: React.ReactNode;
  iconColor?: string;
  fillColor?: string;
  fillColorHover?: string;
  strokeColor?: string;
  strokeColorHover?: string;
  textColor?: string;
}

interface BaseButtonProps extends CommonButtonProps, React.ComponentPropsWithRef<'button'> {}

export const BaseButton = React.forwardRef(
  (props: BaseButtonProps, ref: React.ForwardedRef<HTMLButtonElement>) => {
    const {
      fillColor = Colors.backgroundDefault(),
      fillColorHover = Colors.backgroundDefaultHover(),
      disabled,
      icon,
      label,
      loading,
      rightIcon,
      iconColor = Colors.accentReversed(),
      textColor = Colors.textDefault(),
      strokeColor = Colors.accentGray(),
      strokeColorHover = Colors.accentGray(),
      ...rest
    } = props;

    return (
      <StyledButton
        {...rest}
        as="button"
        disabled={!!(disabled || loading)}
        $iconColor={iconColor}
        $fillColor={fillColor}
        $fillColorHover={fillColorHover}
        $strokeColor={strokeColor}
        $strokeColorHover={strokeColorHover}
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

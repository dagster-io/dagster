import * as React from 'react';

import {Colors} from './Colors';
import {StyledButton, StyledButtonText} from './StyledButton';

interface CommonButtonProps {
  icon?: React.ReactNode;
  label?: React.ReactNode;
  loading?: boolean;
  rightIcon?: React.ReactNode;
  fillColor?: string;
  strokeColor?: string;
  textColor?: string;
}

interface BaseButtonProps extends CommonButtonProps, React.ComponentPropsWithRef<'button'> {}

export const BaseButton = React.forwardRef(
  (props: BaseButtonProps, ref: React.ForwardedRef<HTMLButtonElement>) => {
    const {
      fillColor = Colors.White,
      disabled,
      icon,
      label,
      loading,
      rightIcon,
      textColor = Colors.Dark,
      strokeColor = Colors.Gray300,
      ...rest
    } = props;

    return (
      <StyledButton
        {...rest}
        as="button"
        disabled={!!(disabled || loading)}
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

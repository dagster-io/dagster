import * as React from 'react';
import styled, {css} from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {IconWrapper} from './Icon';

interface Props extends React.ComponentPropsWithRef<'button'> {
  icon?: React.ReactNode;
  label?: React.ReactNode;
  loading?: boolean;
  rightIcon?: React.ReactNode;
  fillColor?: string;
  stroke?: boolean;
  textColor?: string;
}

export const BaseButton = React.forwardRef(
  (props: Props, ref: React.ForwardedRef<HTMLButtonElement>) => {
    const {
      fillColor = ColorsWIP.White,
      disabled,
      icon,
      label,
      loading,
      rightIcon,
      textColor = ColorsWIP.Dark,
      stroke = true,
      ...rest
    } = props;

    return (
      <StyledButton
        {...rest}
        disabled={disabled || loading}
        $fillColor={fillColor}
        $stroke={stroke}
        $textColor={textColor}
        ref={ref}
      >
        {icon || null}
        {label ? <span>{label}</span> : null}
        {rightIcon || null}
      </StyledButton>
    );
  },
);

interface StyledButtonProps {
  $fillColor: string;
  $stroke: boolean;
  $textColor: string;
}

const backgroundColorCSS = (props: StyledButtonProps) => {
  const {$fillColor} = props;
  if ($fillColor) {
    return $fillColor;
  }
  return 'transparent';
};

const DEFAULT_STROKE = css`
  box-shadow: rgba(0, 0, 0, 0) 0px 1px 1px 0px, ${ColorsWIP.Gray300} 0px 0px 0px 1px;
`;
const NO_STROKE = css`
  box-shadow: rgba(0, 0, 0, 0) 0px 1px 1px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 1px;
`;
const DEFAULT_STROKE_PLUS_HOVER = css`
  box-shadow: rgb(0, 0, 0, 0) 0px 1px 1px 0px, ${ColorsWIP.Gray400} 0px 0px 0px 1px,
    rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
`;
const NO_STROKE_PLUS_HOVER = css`
  box-shadow: rgba(0, 0, 0, 0) 0px 1px 1px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 1px,
    rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
`;

const boxShadowCSS = (props: StyledButtonProps) => {
  const {$stroke} = props;
  if ($stroke) {
    return DEFAULT_STROKE;
  }
  return NO_STROKE;
};

const textColorCSS = (props: StyledButtonProps) => {
  const {$textColor} = props;
  if ($textColor) {
    return $textColor;
  }
  return ColorsWIP.Dark;
};

const StyledButton = styled.button<StyledButtonProps>`
  align-items: center;
  background-color: ${backgroundColorCSS};
  border: none;
  border-radius: 8px;
  color: ${textColorCSS};
  cursor: pointer;
  display: inline-flex;
  flex-direction: row;
  font-size: 14px;
  line-height: 20px;
  padding: 6px 12px;
  transition: background 100ms, box-shadow 150ms;
  user-select: none;

  ${boxShadowCSS}

  :hover {
    ${({$stroke}) => ($stroke ? DEFAULT_STROKE_PLUS_HOVER : NO_STROKE_PLUS_HOVER)};
  }

  :focus {
    box-shadow: rgba(0, 0, 0, 0) 0px 1px 1px 0px, rgba(58, 151, 212, 0.6) 0 0 0 3px;
    outline: none;
  }

  :disabled {
    cursor: default;
    opacity: 0.5;
  }

  :disabled:hover {
    ${({$stroke}) => ($stroke ? DEFAULT_STROKE : null)};
  }

  ${IconWrapper} {
    color: ${textColorCSS};
    align-self: center;
    display: block;
  }

  ${IconWrapper}:first-child {
    margin-left: -4px;
    margin-right: 4px;
  }

  ${IconWrapper}:last-child {
    margin-right: -4px;
    margin-left: 4px;
  }

  ${IconWrapper}:first-child:last-child {
    margin: 2px -4px;
  }
`;

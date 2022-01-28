import * as React from 'react';
import styled, {css} from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {IconName, IconWIP, IconWrapper} from './Icon';
import {FontFamily} from './styles';

interface Props extends Omit<React.ComponentPropsWithRef<'input'>, 'type' | 'onChange'> {
  icon?: IconName;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  strokeColor?: string;
  rightElement?: JSX.Element;
}

export const TextInput = React.forwardRef(
  (props: Props, ref: React.ForwardedRef<HTMLInputElement>) => {
    const {icon, disabled, strokeColor = ColorsWIP.Gray300, rightElement, ...rest} = props;

    return (
      <Container $disabled={!!disabled}>
        {icon ? <IconWIP name={icon} color={ColorsWIP.Gray900} /> : null}
        <StyledInput
          {...rest}
          $strokeColor={strokeColor}
          disabled={disabled}
          ref={ref}
          $hasIcon={!!icon}
          type="text"
        />
        {rightElement ? rightElement : null}
      </Container>
    );
  },
);

TextInput.displayName = 'TextInput';

const Container = styled.div<{$disabled: boolean}>`
  align-items: center;
  color: ${ColorsWIP.Gray600};
  display: inline-flex;
  flex-direction: row;
  flex: 1;
  flex-grow: 0;
  font-family: ${FontFamily.default};
  font-size: 14px;
  font-weight: 400;
  position: relative;

  ${IconWrapper}:first-child {
    position: absolute;
    left: 8px;
    top: 8px;
    ${({$disabled}) =>
      $disabled
        ? css`
            background-color: ${ColorsWIP.Gray400};
          `
        : null};
  }
`;

interface StyledInputProps {
  $hasIcon: boolean;
  $strokeColor: string;
}

const StyledInput = styled.input<StyledInputProps>`
  border: none;
  border-radius: 8px;
  box-shadow: ${({$strokeColor}) => $strokeColor} inset 0px 0px 0px 1px,
    ${ColorsWIP.KeylineGray} inset 2px 2px 1.5px;
  flex-grow: 1;
  line-height: 20px;
  padding: ${({$hasIcon}) => ($hasIcon ? '6px 6px 6px 28px' : '6px 6px 6px 12px')};
  margin: 0;
  transition: box-shadow 150ms;

  :disabled {
    box-shadow: ${ColorsWIP.Gray200} inset 0px 0px 0px 1px,
      ${ColorsWIP.KeylineGray} inset 2px 2px 1.5px;
    background-color: ${ColorsWIP.Gray50};
    color: ${ColorsWIP.Gray400};
  }

  :disabled::placeholder {
    color: ${ColorsWIP.Gray400};
  }

  :focus {
    box-shadow: ${({$strokeColor}) => $strokeColor} inset 0px 0px 0px 1px,
      ${ColorsWIP.KeylineGray} inset 2px 2px 1.5px, rgba(58, 151, 212, 0.6) 0 0 0 3px;
    outline: none;
  }
`;

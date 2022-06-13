import * as React from 'react';
import styled, {css} from 'styled-components/macro';

import {Colors} from './Colors';
import {IconName, Icon, IconWrapper} from './Icon';
import {FontFamily} from './styles';

interface Props extends Omit<React.ComponentPropsWithRef<'input'>, 'onChange'> {
  icon?: IconName;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  strokeColor?: string;
  rightElement?: JSX.Element;
}

export const TextInput = React.forwardRef(
  (props: Props, ref: React.ForwardedRef<HTMLInputElement>) => {
    const {
      icon,
      disabled,
      strokeColor = Colors.Gray300,
      rightElement,
      type = 'text',
      ...rest
    } = props;

    return (
      <Container $disabled={!!disabled}>
        {icon ? <Icon name={icon} color={Colors.Gray900} /> : null}
        <StyledInput
          {...rest}
          $strokeColor={strokeColor}
          disabled={disabled}
          ref={ref}
          $hasIcon={!!icon}
          type={type}
        />
        {rightElement ? <RightContainer>{rightElement}</RightContainer> : null}
      </Container>
    );
  },
);

TextInput.displayName = 'TextInput';

export const TextInputContainerStyles = css`
  align-items: center;
  color: ${Colors.Gray600};
  display: inline-flex;
  flex-direction: row;
  flex: 1;
  flex-grow: 0;
  font-family: ${FontFamily.default};
  font-size: 14px;
  font-weight: 400;
  position: relative;
`;

const Container = styled.div<{$disabled: boolean}>`
  ${TextInputContainerStyles}

  > ${IconWrapper}:first-child {
    position: absolute;
    left: 8px;
    top: 8px;
    ${({$disabled}) =>
      $disabled
        ? css`
            background-color: ${Colors.Gray400};
          `
        : null};
  }
`;

const RightContainer = styled.div`
  position: absolute;
  bottom: 0;
  top: 0;
  right: 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;
`;

export const TextInputStyles = css`
  border: none;
  border-radius: 8px;
  box-shadow: ${Colors.Gray300} inset 0px 0px 0px 1px, ${Colors.KeylineGray} inset 2px 2px 1.5px;
  flex-grow: 1;
  font-size: 14px;
  line-height: 20px;
  padding: 6px 6px 6px 12px;
  margin: 0;
  transition: box-shadow 150ms;

  :disabled {
    box-shadow: ${Colors.Gray200} inset 0px 0px 0px 1px, ${Colors.KeylineGray} inset 2px 2px 1.5px;
    background-color: ${Colors.Gray50};
    color: ${Colors.Gray400};
  }

  :disabled::placeholder {
    color: ${Colors.Gray400};
  }

  :focus {
    box-shadow: ${Colors.Gray300} inset 0px 0px 0px 1px, ${Colors.KeylineGray} inset 2px 2px 1.5px,
      rgba(58, 151, 212, 0.6) 0 0 0 3px;
    outline: none;
  }
`;

interface StyledInputProps {
  $hasIcon: boolean;
  $strokeColor: string;
}

const StyledInput = styled.input<StyledInputProps>`
  ${TextInputStyles}

  box-shadow: ${({$strokeColor}) => $strokeColor} inset 0px 0px 0px 1px,
    ${Colors.KeylineGray} inset 2px 2px 1.5px;
  padding: ${({$hasIcon}) => ($hasIcon ? '6px 6px 6px 28px' : '6px 6px 6px 12px')};

  :focus {
    box-shadow: ${({$strokeColor}) => $strokeColor} inset 0px 0px 0px 1px,
      ${Colors.KeylineGray} inset 2px 2px 1.5px, rgba(58, 151, 212, 0.6) 0 0 0 3px;
  }
`;

interface TextAreaProps {
  $resize: React.CSSProperties['resize'];
}

export const TextArea = styled.textarea<TextAreaProps>`
  ${TextInputStyles}

  ${({$resize}) => ($resize ? `resize: ${$resize};` : null)}
`;

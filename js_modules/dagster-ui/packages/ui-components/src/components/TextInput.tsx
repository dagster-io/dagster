import * as React from 'react';
import styled, {css} from 'styled-components';

import {
  colorAccentGray,
  colorAccentPrimary,
  colorBackgroundDefault,
  colorBackgroundDisabled,
  colorBorderDefault,
  colorBorderHover,
  colorBorderDisabled,
  colorBorderFocused,
  colorKeylineDefault,
  colorTextDefault,
  colorTextDisabled,
  colorTextLight,
  colorTextLighter,
  colorBackgroundDefaultHover,
  colorAccentLavender,
} from '../theme/color';

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
      strokeColor = colorBorderDefault(),
      rightElement,
      type = 'text',
      ...rest
    } = props;

    return (
      <TextInputContainer $disabled={!!disabled}>
        {icon ? (
          <Icon name={icon} color={disabled ? colorAccentGray() : colorAccentPrimary()} />
        ) : null}
        <StyledInput
          {...rest}
          $strokeColor={strokeColor}
          disabled={disabled}
          ref={ref}
          $hasIcon={!!icon}
          $hasRightElement={!!rightElement}
          type={type}
        />
        {rightElement ? <RightContainer>{rightElement}</RightContainer> : null}
      </TextInputContainer>
    );
  },
);

TextInput.displayName = 'TextInput';

export const TextInputContainerStyles = css`
  align-items: center;
  color: ${colorTextLight()};
  display: inline-flex;
  flex-direction: row;
  flex: 1;
  flex-grow: 0;
  font-family: ${FontFamily.default};
  font-size: 14px;
  font-weight: 400;
  position: relative;
`;

export const TextInputContainer = styled.div<{$disabled?: boolean}>`
  ${TextInputContainerStyles}

  > ${IconWrapper}:first-child {
    position: absolute;
    left: 8px;
    top: 8px;
    ${({$disabled}) =>
      $disabled
        ? css`
            background-color: ${colorBackgroundDisabled()};
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
  background-color: ${colorBackgroundDefault()};
  border: none;
  box-shadow: ${colorBorderDefault()} inset 0px 0px 0px 1px;
  outline: none;
  border-radius: 8px;
  color: ${colorTextDefault()};
  flex-grow: 1;
  font-size: 14px;
  line-height: 20px;
  padding: 6px 6px 6px 12px;
  margin: 0;
  transition: box-shadow linear 150ms;

  ::placeholder {
    color: ${colorTextLighter()};
  }

  :disabled {
    box-shadow:
      ${colorBorderDisabled()} inset 0px 0px 0px 1px,
      ${colorKeylineDefault()} inset 2px 2px 1.5px;
    background-color: ${colorBackgroundDisabled()};
    color: ${colorTextDisabled()};
  }

  :disabled::placeholder {
    color: ${colorTextDisabled()};
  }

  :focus {
    box-shadow:
      ${colorBorderDefault()} inset 0px 0px 0px 1px,
      ${colorKeylineDefault()} inset 2px 2px 1.5px,
      ${colorBorderFocused()} 0 0 0 2px;
      outline: none;
  }
`;

interface StyledInputProps {
  $hasIcon: boolean;
  $strokeColor: string;
  $hasRightElement: boolean;
}

const StyledInput = styled.input<StyledInputProps>`
  ${TextInputStyles}

  ${({$hasRightElement}) =>
    $hasRightElement
      ? css`
          & {
            padding-right: 28px;
          }
        `
      : null}

  box-shadow: ${({$strokeColor}) => $strokeColor || colorBorderDefault()} 0px 0px 0px 1px;
  padding: ${({$hasIcon}) => ($hasIcon ? '6px 6px 6px 28px' : '6px 6px 6px 12px')};

  :hover {
    box-shadow: ${({$strokeColor}) => $strokeColor || colorBorderHover()} 0px 0px 0px 1px;
  }

  :focus {
    box-shadow:
      ${({$strokeColor}) => $strokeColor || colorBorderDefault()} 0px 0px 0px 1px;
      ${colorBorderFocused()} 0 0 0 2px;
      background-color: ${colorBackgroundDefaultHover()};
  }
`;

interface TextAreaProps {
  $resize: React.CSSProperties['resize'];
  $strokeColor?: string;
}

export const TextArea = styled.textarea<TextAreaProps>`
  ${TextInputStyles}

  box-shadow: ${colorBorderDefault()} inset 0px 0px 0px 1px;

  :hover {
    box-shadow: ${colorBorderHover()} inset 0px 0px 0px 1px;
  }

  :hover {
    box-shadow: ${colorBorderHover()} inset 0px 0px 0px 1px;
  }
  :focus {
    box-shadow: ${colorBorderFocused()} 0px 0px 0px 1px;
    background-color: ${colorBackgroundDefaultHover()};
  }

  ${({$resize}) => ($resize ? `resize: ${$resize};` : null)}
`;

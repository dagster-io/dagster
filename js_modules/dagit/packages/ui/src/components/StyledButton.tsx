import styled from 'styled-components/macro';

import {IconWrapper} from './Icon';
import {SpinnerWrapper} from './Spinner';
import {FontFamily} from './styles';

interface StyledButtonProps {
  $fillColor: string;
  $strokeColor: string;
  $textColor: string;
}

export const StyledButton = styled.button<StyledButtonProps>`
  align-items: center;
  background-color: ${({$fillColor}) => $fillColor || 'transparent'};
  border: none;
  border-radius: 8px;
  color: ${({$textColor}) => $textColor};
  cursor: pointer;
  display: inline-flex;
  flex-direction: row;
  font-family: ${FontFamily.default};
  font-size: 14px;
  line-height: 20px;
  padding: 6px 12px;
  transition: background 100ms, box-shadow 150ms, filter 100ms, opacity 150ms;
  user-select: none;
  white-space: nowrap;

  box-shadow: ${({$strokeColor}) => `${$strokeColor} inset 0px 0px 0px 1px`};

  :hover {
    box-shadow: ${({$strokeColor}) =>
      `${$strokeColor} inset 0px 0px 0px 1px, rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;`};
    color: ${({$textColor}) => $textColor};
    text-decoration: none;
  }

  :focus {
    box-shadow: rgba(58, 151, 212, 0.6) 0 0 0 3px;
    outline: none;
  }

  :focus:not(:focus-visible) {
    box-shadow: ${({$strokeColor}) =>
      `${$strokeColor} inset 0px 0px 0px 1px, rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;`};
  }

  :active:not(:disabled) {
    filter: brightness(0.95);
  }

  :disabled {
    cursor: default;
    opacity: 0.5;
  }

  :disabled:hover {
    box-shadow: ${({$strokeColor}) => `${$strokeColor} inset 0px 0px 0px 1px`};
  }

  ${SpinnerWrapper} {
    align-self: center;
    display: block;
  }

  ${IconWrapper} {
    color: ${({$textColor}) => $textColor};
    background-color: ${({$textColor}) => $textColor};
    align-self: center;
    display: block;
  }

  ${SpinnerWrapper}:first-child,
  ${IconWrapper}:first-child {
    margin-left: -4px;
    margin-right: 4px;
  }

  ${SpinnerWrapper}:last-child,
  ${IconWrapper}:last-child {
    margin-right: -4px;
    margin-left: 4px;
  }

  ${SpinnerWrapper}:first-child:last-child {
    margin: 2px -4px;
  }
  ${IconWrapper}:first-child:last-child {
    margin: 2px -4px;
  }
`;

export const StyledButtonText = styled.span`
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

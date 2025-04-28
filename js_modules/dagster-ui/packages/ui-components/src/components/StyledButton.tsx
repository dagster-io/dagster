import styled from 'styled-components';

import {Colors} from './Color';
import {IconWrapper} from './Icon';
import {SpinnerWrapper} from './Spinner';
import {FontFamily} from './styles';

interface StyledButtonProps {
  $fillColor: string;
  $fillColorHover?: string;
  $strokeColor: string;
  $strokeColorHover?: string;
  $textColor: string;
  $iconColor: string;
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
  transition:
    background 100ms,
    box-shadow 150ms,
    filter 100ms,
    opacity 150ms;
  user-select: none;
  white-space: nowrap;

  box-shadow: ${({$strokeColor}) => `${$strokeColor} inset 0px 0px 0px 1px`};

  :hover:not(:disabled) {
    background-color: ${({$fillColor, $fillColorHover}) =>
      $fillColorHover || $fillColor || 'transparent'};
    box-shadow: ${({$strokeColor, $strokeColorHover}) =>
      `${
        $strokeColorHover || $strokeColor
      } inset 0px 0px 0px 1px, ${Colors.shadowDefault()} 0px 2px 12px 0px;`};
    color: ${({$textColor}) => $textColor};
    text-decoration: none;
  }

  :focus,
  :focus-visible,
  :focus:hover:not(:disabled) {
    box-shadow: ${Colors.focusRing()} 0 0 0 2px;
    outline: none;
  }

  :focus:not(:focus-visible) {
    box-shadow: ${({$strokeColor}) =>
      `${$strokeColor} inset 0px 0px 0px 1px, ${Colors.shadowDefault()} 0px 2px 12px 0px;`};
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
    color: ${({$iconColor}) => $iconColor};
    background-color: ${({$iconColor}) => $iconColor};
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
  text-align: left;
  flex: 1;
`;

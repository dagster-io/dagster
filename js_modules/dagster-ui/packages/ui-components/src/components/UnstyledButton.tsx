import styled, {css} from 'styled-components';

import {colorTextDefault, colorBorderFocused} from '../theme/color';

interface Props {
  $expandedClickPx?: number;
  $showFocusOutline?: boolean;
}

export const UnstyledButton = styled.button<Props>`
  border: 0;
  background-color: transparent;
  border-radius: 4px;
  color: ${colorTextDefault()};
  cursor: pointer;
  padding: 0;
  text-align: start;
  transition:
    box-shadow 150ms,
    opacity 150ms;
  user-select: none;
  white-space: nowrap;

  ${({$expandedClickPx}) =>
    $expandedClickPx
      ? css`
          padding: ${$expandedClickPx}px;
          margin: -${$expandedClickPx}px;
        `
      : null}

  :focus,
  :active {
    outline: none;
    ${({$showFocusOutline}) =>
      $showFocusOutline ? `box-shadow: ${colorBorderFocused()} 0 0 0 2px;
      ` : null}
  }

  &:disabled {
    color: inherit;
    cursor: default;
    opacity: 0.6;
  }
`;

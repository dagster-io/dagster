import styled, {css} from 'styled-components';

import {Colors} from './Color';

interface Props {
  $expandedClickPx?: number;
}

export const UnstyledButton = styled.button<Props>`
  border: 0;
  background-color: transparent;
  border-radius: 4px;
  color: ${Colors.textDefault()};
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

  &:disabled {
    color: inherit;
    cursor: default;
    opacity: 0.6;
  }
`;

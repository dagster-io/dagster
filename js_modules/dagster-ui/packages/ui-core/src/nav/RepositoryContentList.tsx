import {
  colorBackgroundBlue,
  colorBackgroundLighter,
  colorBorderDefault,
  colorTextBlue,
  colorTextDefault,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

export const Item = styled(Link)<{$active: boolean}>`
  background-color: ${({$active}) => ($active ? colorBackgroundBlue() : 'transparent')};
  border-radius: 8px;
  font-size: 14px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 6px 12px;
  display: flex;
  gap: 6px;
  align-items: center;
  color: ${({$active}) => ($active ? colorTextBlue() : colorTextDefault())} !important;
  user-select: none;
  transition:
    background 50ms linear,
    color 50ms linear;

  &:hover {
    text-decoration: none;
    background-color: ${({$active}) =>
      $active ? colorBackgroundBlue() : colorBackgroundLighter()};
  }

  &:focus {
    outline: 0;
  }

  &.focused {
    border-left: 4px solid ${colorBorderDefault()};
  }
`;

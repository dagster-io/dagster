import {Colors} from '@dagster-io/ui';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

export const Items = styled.div`
  flex: 1;
  overflow: auto;
  padding: 0 12px;
  &::-webkit-scrollbar {
    width: 8px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${Colors.Gray200} ${Colors.Gray200};

  &::-webkit-scrollbar-track {
    background: ${Colors.Gray100};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${Colors.Gray200};
    border-radius: 6px;
    border: 3px solid ${Colors.Gray200};
  }
`;

export const Item = styled(Link)<{$active: boolean}>`
  background-color: ${({$active}) => ($active ? Colors.Blue50 : 'transparent')};
  border-radius: 8px;
  font-size: 14px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 6px 12px;
  display: flex;
  gap: 6px;
  align-items: center;
  color: ${({$active}) => ($active ? Colors.Blue700 : Colors.Dark)} !important;
  user-select: none;
  transition: background 50ms linear, color 50ms linear;

  &:hover {
    text-decoration: none;
    background-color: ${({$active}) => ($active ? Colors.Blue50 : Colors.Gray10)};
  }

  &:focus {
    outline: 0;
  }

  &.focused {
    border-left: 4px solid ${Colors.Gray400};
  }
`;

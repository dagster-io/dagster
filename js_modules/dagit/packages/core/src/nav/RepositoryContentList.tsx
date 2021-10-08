import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';

export const Items = styled.div`
  flex: 1;
  overflow: auto;
  padding: 0 12px;
  &::-webkit-scrollbar {
    width: 8px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${ColorsWIP.Gray200} ${ColorsWIP.Gray200};

  &::-webkit-scrollbar-track {
    background: ${ColorsWIP.Gray100};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${ColorsWIP.Gray200};
    border-radius: 6px;
    border: 3px solid ${ColorsWIP.Gray200};
  }
`;

export const Item = styled(Link)`
  border-radius: 8px;
  font-size: 14px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 6px 12px;
  display: block;
  color: ${ColorsWIP.Gray900} !important;
  user-select: none;

  &:hover {
    text-decoration: none;
  }

  &:focus {
    outline: 0;
  }

  &.focused {
    border-left: 4px solid ${ColorsWIP.Gray400};
  }

  &.selected {
    background: ${ColorsWIP.Gray200};
  }
`;

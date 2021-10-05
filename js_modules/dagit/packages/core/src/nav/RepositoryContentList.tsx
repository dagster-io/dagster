import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';

export const Items = styled.div`
  flex: 1;
  overflow: auto;
  &::-webkit-scrollbar {
    width: 11px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${ColorsWIP.Gray600} ${ColorsWIP.Gray900};

  &::-webkit-scrollbar-track {
    background: ${ColorsWIP.Gray900};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${ColorsWIP.Gray600};
    border-radius: 6px;
    border: 3px solid ${ColorsWIP.Gray900};
  }
`;

export const Item = styled(Link)`
  font-size: 13px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 8px 12px;
  padding-left: 8px;
  border-left: 4px solid transparent;
  border-bottom: 1px solid transparent;
  display: block;
  color: ${ColorsWIP.Gray100} !important;
  user-select: none;

  &:hover {
    text-decoration: none;
    color: ${ColorsWIP.White} !important;
  }
  &:focus {
    outline: 0;
  }
  &.focused {
    border-left: 4px solid ${ColorsWIP.Gray400};
  }
  &.selected {
    border-left: 4px solid ${ColorsWIP.Blue500};
    border-bottom: 1px solid ${ColorsWIP.Gray900};
    background: ${ColorsWIP.Dark};
    font-weight: 600;
    color: ${ColorsWIP.White} !important;
  }
`;

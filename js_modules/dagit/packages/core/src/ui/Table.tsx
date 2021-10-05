import {HTMLTable, IHTMLTableProps} from '@blueprintjs/core';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {FontFamily} from './styles';

interface TableProps extends IHTMLTableProps {
  $compact?: boolean;
}

export const Table = styled(HTMLTable)<TableProps>`
  border: none;
  width: 100%;

  & tr th,
  & tr td {
    box-shadow: inset 0 1px 0 rgba(35, 31, 27, 0.1), inset 1px 0 0 rgba(35, 31, 27, 0.1) !important;
  }

  & tr th {
    color: ${ColorsWIP.Gray500};
    font-family: ${FontFamily.default};
    font-size: 12px;
    font-weight: 400;
    padding: ${({$compact}) => ($compact ? '8px' : '6px 24px')};
    vertical-align: bottom;
  }

  & tr td {
    color: ${ColorsWIP.Gray900};
    font-family: ${FontFamily.monospace};
    font-size: 16px;
    padding: ${({$compact}) => ($compact ? '8px' : '6px 24px')};
  }

  & tr:last-child td {
    box-shadow: inset 0 1px 0 rgba(35, 31, 27, 0.1), inset 1px 0 0 rgba(35, 31, 27, 0.1),
      inset 0 -1px 0 rgba(35, 31, 27, 0.1) !important;
  }
`;

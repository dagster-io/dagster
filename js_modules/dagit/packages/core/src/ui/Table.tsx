import {HTMLTable, IHTMLTableProps} from '@blueprintjs/core';
import styled from 'styled-components/macro';

import {StyledTag} from './BaseTag';
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
    box-shadow: inset 0 1px 0 ${ColorsWIP.KeylineGray}, inset 1px 0 0 ${ColorsWIP.KeylineGray} !important;
  }

  & tr th {
    color: ${ColorsWIP.Gray500};
    font-family: ${FontFamily.default};
    font-size: 12px;
    font-weight: 400;
    padding: ${({$compact}) => ($compact ? '0 8px' : ' 8px 12px')};
    min-height: 32px;
    white-space: nowrap;
    vertical-align: bottom;
  }
  & tr th:first-child {
    padding-left: ${({$compact}) => ($compact ? '8px' : ' 24px')};
  }

  & tr td {
    color: ${ColorsWIP.Gray900};
    font-family: ${FontFamily.monospace};
    font-size: 16px;
    padding: ${({$compact}) => ($compact ? '8px' : '12px')};
  }
  & tr td:first-child {
    padding-left: ${({$compact}) => ($compact ? '8px' : ' 24px')};
  }

  & tr:last-child td {
    box-shadow: inset 0 1px 0 ${ColorsWIP.KeylineGray}, inset 1px 0 0 ${ColorsWIP.KeylineGray},
      inset 0 -1px 0 ${ColorsWIP.KeylineGray} !important;
  }

  & tr td ${StyledTag} {
    font-family: ${FontFamily.default};
  }
`;

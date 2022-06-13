// eslint-disable-next-line no-restricted-imports
import {HTMLTable, IHTMLTableProps} from '@blueprintjs/core';
import styled from 'styled-components/macro';

import {StyledTag} from './BaseTag';
import {Colors} from './Colors';
import {FontFamily} from './styles';

export interface TableProps extends IHTMLTableProps {
  $compact?: boolean;
}

export const Table = styled(HTMLTable)<TableProps>`
  border: none;
  width: 100%;

  & tr th {
    color: ${Colors.Gray500};
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

  & tr th:last-child,
  & tr td:last-child {
    border-right: 1px solid ${Colors.KeylineGray};
  }

  & tr td {
    color: ${Colors.Gray900};
    font-family: ${FontFamily.monospace};
    font-size: 16px;
    padding: ${({$compact}) => ($compact ? '8px' : '12px')};
  }

  & tr td:first-child {
    padding-left: ${({$compact}) => ($compact ? '8px' : ' 24px')};
  }

  & tr:last-child td {
    box-shadow: inset 0 1px 0 ${Colors.KeylineGray}, inset 1px 0 0 ${Colors.KeylineGray},
      inset 0 -1px 0 ${Colors.KeylineGray} !important;
  }

  & tr td ${StyledTag} {
    font-family: ${FontFamily.default};
  }
`;

import {HTMLTable, Colors, IHTMLTableProps} from '@blueprintjs/core';
import styled from 'styled-components';

interface TableProps extends IHTMLTableProps {
  $compact?: boolean;
}

export const Table = styled(HTMLTable)<TableProps>`
  border: none;
  width: 100%;

  & tbody tr {
    box-shadow: inset 0 1px ${Colors.LIGHT_GRAY3};
  }

  & tr th {
    box-shadow: none !important;
    color: ${Colors.GRAY2};
    font-size: 12px;
    padding: ${({$compact}) => ($compact ? '8px 8px 8px 0' : '12px 24px 12px 0')};
    text-transform: uppercase;
    vertical-align: bottom;
  }

  & tr td {
    box-shadow: none !important;
    padding: ${({$compact}) => ($compact ? '8px 8px 8px 0' : '12px 24px 12px 0')};
  }

  & tr td:first-child,
  & tr th:first-child {
    padding-left: 0;
  }

  & tr td:last-child,
  & tr th:last-child {
    padding-right: 0;
  }
`;

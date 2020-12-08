import {HTMLTable, Colors} from '@blueprintjs/core';
import styled from 'styled-components';

export const Table = styled(HTMLTable)`
  & tr th {
    color: ${Colors.GRAY3};
    font-size: 12px;
    padding: 8px;
    text-transform: uppercase;
    vertical-align: bottom;
  }

  & tr td {
    padding: 8px;
  }
`;

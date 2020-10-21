import {HTMLTable, Colors} from '@blueprintjs/core';
import styled from 'styled-components';

export const Table = styled(HTMLTable)`
  & tr th {
    color: ${Colors.GRAY3};
    font-size: 12px;
    text-transform: uppercase;
    vertical-align: bottom;
  }

  & tr td,
  tr td div {
    overflow: hidden;
    white-space: nowrap;
  }
`;

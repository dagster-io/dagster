import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';

type Row = {key: string; value: React.ReactNode};

interface Props {
  rows: (Row | null | undefined)[];
  spacing: 0 | 2 | 4;
}

export const MetadataTable = (props: Props) => {
  const {rows, spacing} = props;

  return (
    <StyledTable>
      <tbody>
        {rows.filter(Boolean).map((pair: Row) => {
          const {key, value} = pair;
          return (
            <tr key={key}>
              <td>
                <Box padding={{vertical: spacing, right: 32}}>
                  <MetadataKey>{key}</MetadataKey>
                </Box>
              </td>
              <td>
                <Box padding={{vertical: spacing}}>{value}</Box>
              </td>
            </tr>
          );
        })}
      </tbody>
    </StyledTable>
  );
};

MetadataTable.defaultProps = {
  spacing: 4,
};

const StyledTable = styled.table`
  border-spacing: 0;
  td {
    vertical-align: top;
  }

  td .bp3-control {
    margin-bottom: 0;
  }
`;

export const MetadataKey = styled.div`
  color: ${Colors.GRAY1};
  font-weight: 400;
`;

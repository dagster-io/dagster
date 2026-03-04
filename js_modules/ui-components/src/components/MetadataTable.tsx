import * as React from 'react';
import styled from 'styled-components';

import {Box} from './Box';
import {Table, TableProps} from './Table';

export type MetadataTableRow = {key: string; label?: React.ReactNode; value: React.ReactNode};

interface Props {
  rows: (MetadataTableRow | null | undefined)[];
  spacing?: 0 | 2 | 4;
}

export const MetadataTable = (props: Props) => {
  const {rows, spacing = 4} = props;

  return (
    <StyledTable>
      <tbody>
        {rows.map((pair: MetadataTableRow | null | undefined) => {
          if (!pair) {
            return null;
          }
          const {key, label, value} = pair;
          return (
            <tr key={key}>
              <td>
                <Box padding={{vertical: spacing, right: 32}}>
                  <MetadataKey>{label ?? key}</MetadataKey>
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

export const StyledTable = styled.table`
  border-spacing: 0;
  td {
    vertical-align: top;
  }

  td .bp5-control {
    margin-bottom: 0;
  }
`;

const MetadataKey = styled.div`
  font-weight: 400;
`;

export const MetadataTableWIP = styled(Table)<TableProps>`
  td:first-child {
    white-space: nowrap;
    width: 1px;
    max-width: 400px;
    word-break: break-word;
    overflow: hidden;
    padding-right: 24px;
    text-overflow: ellipsis;
  }
`;

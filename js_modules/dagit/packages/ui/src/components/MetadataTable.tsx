import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Colors} from './Colors';
import {Table, TableProps} from './Table';

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
        {rows.map((pair: Row | null | undefined) => {
          if (!pair) {
            return null;
          }
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

export const StyledTable = styled.table`
  border-spacing: 0;
  td {
    vertical-align: top;
  }

  td .bp3-control {
    margin-bottom: 0;
  }
`;

const MetadataKey = styled.div`
  color: ${Colors.Gray600};
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

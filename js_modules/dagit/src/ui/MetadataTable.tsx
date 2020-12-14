import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';

type Row = {key: string; value: React.ReactNode};

interface Props {
  rows: (Row | null | undefined)[];
}

export const MetadataTable: React.FC<Props> = (props) => {
  const {rows} = props;

  return (
    <StyledTable>
      <tbody>
        {rows.filter(Boolean).map((pair: Row) => {
          const {key, value} = pair;
          return (
            <tr key={key}>
              <td>
                <Box padding={{vertical: 4, right: 32}}>
                  <Key>{key}</Key>
                </Box>
              </td>
              <td>
                <Box padding={{vertical: 4}}>{value}</Box>
              </td>
            </tr>
          );
        })}
      </tbody>
    </StyledTable>
  );
};

const StyledTable = styled.table`
  border-spacing: 0;
`;

const Key = styled.div`
  color: ${Colors.GRAY1};
  font-weight: 400;
`;

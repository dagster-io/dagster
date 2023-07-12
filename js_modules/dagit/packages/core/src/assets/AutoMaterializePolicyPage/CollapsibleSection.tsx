import {Box, Colors, Icon, Subheading} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

interface Props {
  header: React.ReactNode;
  headerRightSide?: React.ReactNode;
  children: React.ReactNode;
}

export const CollapsibleSection = ({header, headerRightSide, children}: Props) => {
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  return (
    <Box
      flex={{direction: 'column'}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <SectionHeader onClick={() => setIsCollapsed(!isCollapsed)}>
        <Box
          flex={{
            justifyContent: 'space-between',
            gap: 12,
            grow: 1,
          }}
          padding={{vertical: 8, horizontal: 16}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4, grow: 1}}>
            <Icon
              name="arrow_drop_down"
              style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
            />
            <Subheading>{header}</Subheading>
          </Box>
          {headerRightSide}
        </Box>
      </SectionHeader>
      {isCollapsed ? null : <Box padding={{vertical: 12, left: 32, right: 16}}>{children}</Box>}
    </Box>
  );
};

const SectionHeader = styled.button`
  background-color: ${Colors.White};
  border: 0;
  cursor: pointer;
  padding: 0;
  margin: 0;

  :focus {
    outline: none;
  }
`;

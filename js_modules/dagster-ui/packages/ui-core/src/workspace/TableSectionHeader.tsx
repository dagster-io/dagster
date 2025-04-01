import {Box, Colors, Icon, IconWrapper} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const SECTION_HEADER_HEIGHT = 32;

export interface TableSectionHeaderProps {
  expanded: boolean;
  onClick: (e: React.MouseEvent) => void;
  children?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const TableSectionHeader = (props: TableSectionHeaderProps) => {
  const {expanded, onClick, children, rightElement} = props;
  return (
    <SectionHeaderButton $open={expanded} onClick={onClick}>
      <Box
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
        padding={{horizontal: 24}}
      >
        {children}
        <Box flex={{alignItems: 'center', gap: 8}}>
          {rightElement}
          <Box margin={{top: 2}}>
            <Icon name="arrow_drop_down" />
          </Box>
        </Box>
      </Box>
    </SectionHeaderButton>
  );
};

const SectionHeaderButton = styled.button<{$open: boolean}>`
  background-color: ${Colors.backgroundLight()};
  border: 0;
  box-shadow:
    inset 0px -1px 0 ${Colors.keylineDefault()},
    inset 0px 1px 0 ${Colors.keylineDefault()};
  color: ${Colors.textLight()};
  cursor: pointer;
  display: block;
  padding: 0;
  width: 100%;
  margin: 0;
  height: ${SECTION_HEADER_HEIGHT}px;
  text-align: left;

  :focus,
  :active {
    outline: none;
  }

  :hover {
    background-color: ${Colors.backgroundLightHover()};
  }

  ${IconWrapper}[aria-label="arrow_drop_down"] {
    transition: transform 100ms linear;
    ${({$open}) => ($open ? null : `transform: rotate(-90deg);`)}
  }
`;

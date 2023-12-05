import {Box, Icon, colorBackgroundLight} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

export const ToggleableSection = ({
  isInitiallyOpen,
  title,
  children,
  background,
}: {
  isInitiallyOpen: boolean;
  title: React.ReactNode;
  children: React.ReactNode;
  background?: string;
}) => {
  const [isOpen, setIsOpen] = React.useState(isInitiallyOpen);
  return (
    <Box>
      <Box
        onClick={() => setIsOpen(!isOpen)}
        background={background ?? colorBackgroundLight()}
        border="bottom"
        flex={{alignItems: 'center', direction: 'row'}}
        padding={{vertical: 12, right: 20, left: 16}}
        style={{cursor: 'pointer'}}
      >
        <Rotateable $rotate={!isOpen}>
          <Icon name="arrow_drop_down" />
        </Rotateable>
        <div style={{flex: 1}}>{title}</div>
      </Box>
      {isOpen && <Box>{children}</Box>}
    </Box>
  );
};

const Rotateable = styled.span<{$rotate: boolean}>`
  ${({$rotate}) => ($rotate ? 'transform: rotate(-90deg);' : '')}
`;

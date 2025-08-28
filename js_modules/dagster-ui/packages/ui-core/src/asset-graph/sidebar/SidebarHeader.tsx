import {Box, Button, ButtonGroup, Icon, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

interface SidebarHeaderProps {
  sidebarViewType: 'tree' | 'group';
  setSidebarViewType: (viewType: 'tree' | 'group') => void;
  hideSidebar: () => void;
}

export const SidebarHeader: React.FC<SidebarHeaderProps> = ({
  sidebarViewType,
  setSidebarViewType,
  hideSidebar,
}) => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gap: '6px',
        padding: '12px',
      }}
    >
      <ButtonGroupWrapper>
        <ButtonGroup
          activeItems={new Set([sidebarViewType])}
          buttons={[
            {id: 'group', label: 'Group view', icon: 'asset_group'},
            {id: 'tree', label: 'Tree view', icon: 'gantt_flat'},
          ]}
          onClick={(id: 'tree' | 'group') => {
            setSidebarViewType(id);
          }}
        />
      </ButtonGroupWrapper>
      <Tooltip content="Hide sidebar">
        <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
      </Tooltip>
    </Box>
  );
};

const ButtonGroupWrapper = styled.div`
  > * {
    display: grid;
    grid-template-columns: 1fr 1fr;
    > * {
      place-content: center;
    }
    span {
      flex: initial;
    }
  }
`;

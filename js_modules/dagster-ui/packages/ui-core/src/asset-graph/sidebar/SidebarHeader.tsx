import {Box, Button, ButtonGroup, Icon, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import styles from './SidebarHeader.module.css';

interface SidebarHeaderProps {
  sidebarViewType: 'tree' | 'group';
  setSidebarViewType: (viewType: 'tree' | 'group') => void;
  hideSidebar: () => void;
}

export const SidebarHeader = ({
  sidebarViewType,
  setSidebarViewType,
  hideSidebar,
}: SidebarHeaderProps) => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gap: '6px',
        padding: '12px',
      }}
    >
      <div className={styles.buttonGroupWrapper}>
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
      </div>
      <Tooltip content="Hide sidebar">
        <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
      </Tooltip>
    </Box>
  );
};

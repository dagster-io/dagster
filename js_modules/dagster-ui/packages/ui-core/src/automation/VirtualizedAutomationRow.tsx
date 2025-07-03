import {Box} from '@dagster-io/ui-components';
import {BorderSetting, BorderSide} from '@dagster-io/ui-components/src/components/types';
import React from 'react';

import styles from './css/VirtualizedAutomationRow.module.css';
import {HeaderCell, HeaderRow} from '../ui/VirtualizedTable';

export const TEMPLATE_COLUMNS = '60px minmax(400px, 1.5fr) 240px 1fr 200px 200px';

export const VirtualizedAutomationHeader = ({checkbox}: {checkbox: React.ReactNode}) => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>
        <div style={{position: 'relative', top: '-1px'}}>{checkbox}</div>
      </HeaderCell>
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Type</HeaderCell>
      <HeaderCell>Target</HeaderCell>
      <HeaderCell>Last tick</HeaderCell>
      <HeaderCell>Last run</HeaderCell>
    </HeaderRow>
  );
};

export const AutomationRowGrid = ({
  children,
  ...rest
}: {
  children: React.ReactNode;
  border?: BorderSide | BorderSetting | null;
}) => (
  <Box
    className={styles.automationRowGrid}
    style={{gridTemplateColumns: TEMPLATE_COLUMNS}}
    {...rest}
  >
    {children}
  </Box>
);

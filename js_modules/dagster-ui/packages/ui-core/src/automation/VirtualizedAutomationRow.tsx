import {Box} from '@dagster-io/ui-components';
import {HeaderCell, HeaderRow} from '../ui/VirtualizedTable';
import styles from './VirtualizedAutomationRow.module.css';

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

export const AutomationRowGrid = ({children, ...rest}) => (
  <Box 
    className={styles.automationRowGrid} 
    style={{gridTemplateColumns: TEMPLATE_COLUMNS}} 
    {...rest}
  >
    {children}
  </Box>
);

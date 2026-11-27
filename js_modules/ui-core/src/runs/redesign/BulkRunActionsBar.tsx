import {Box, Button, Icon, Text, Tooltip} from '@dagster-io/ui-components';

import styles from './css/BulkRunActionsBar.module.css';
import {CheckAllBox} from '../../ui/CheckAllBox';
import {numberFormatter} from '../../ui/formatters';
import {RunBulkActionsMenu} from '../RunActionsMenu';
import {RunActionsMenuRunFragment} from '../types/RunActionsMenuRunFragment.types';

type BulkRunActionsBarProps = {
  selectedRuns: RunActionsMenuRunFragment[];
  pageRunCount: number;
  onToggleAll: (checked: boolean) => void;
  clearSelection: () => void;
  onClose: () => void;
};

export const BulkRunActionsBar = ({
  selectedRuns,
  pageRunCount,
  onToggleAll,
  clearSelection,
  onClose,
}: BulkRunActionsBarProps) => {
  const count = selectedRuns.length;

  return (
    <Box flex={{alignItems: 'center', gap: 12}} border="bottom" className={styles.bar}>
      <CheckAllBox
        checkedCount={count}
        totalCount={pageRunCount}
        onToggleAll={onToggleAll}
        size="small"
        className={styles.checkAllBox}
        aria-label="Select all runs on this page"
      />
      <span role="status" className={styles.count}>
        {count === 0 ? (
          <Text size={12} color="textLight">
            Select runs
          </Text>
        ) : (
          <>
            <Text size={12} weight={600}>
              {numberFormatter.format(count)}
            </Text>{' '}
            <Text size={12} color="textLight">
              {count === 1 ? 'run selected' : 'runs selected'}
            </Text>
          </>
        )}
      </span>
      <RunBulkActionsMenu selected={selectedRuns} clearSelection={clearSelection} />
      <Tooltip content="Close and clear selection">
        <Button
          intent="none"
          icon={<Icon name="close" />}
          aria-label="Close and clear selection"
          onClick={onClose}
        />
      </Tooltip>
    </Box>
  );
};

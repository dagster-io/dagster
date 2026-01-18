import {Box, Icon, IconName, Subtitle, UnstyledButton} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useDeferredValue} from 'react';

import styles from './css/SelectionSectionHeader.module.css';
import {numberFormatter} from '../../ui/formatters';

interface Props {
  icon: IconName;
  label: string;
  count: number;
  border: 'top-and-bottom' | 'bottom';
  isOpen: boolean;
  toggleOpen: () => void;
  children?: React.ReactNode;
  displayAs: 'List' | 'Grid';
}

// DRY: Shared Section Header for Selections
export const SelectionSectionHeader = ({
  icon,
  label,
  count,
  border,
  isOpen,
  toggleOpen,
  children,
  displayAs,
}: Props) => {
  const actuallyOpen = useDeferredValue(isOpen);
  return (
    <Box padding={{bottom: actuallyOpen && displayAs === 'Grid' ? 12 : 0}}>
      <Box
        flex={{
          direction: 'row',
          alignItems: 'center',
          gap: 8,
          justifyContent: 'space-between',
        }}
        border={border}
        padding={{right: 24}}
        className={styles.header}
      >
        <UnstyledButton onClick={toggleOpen} className={styles.button}>
          <Box
            flex={{direction: 'row', alignItems: 'center', gap: 8}}
            padding={{horizontal: 24, vertical: 2}}
          >
            <Icon name={icon} />
            <Subtitle>
              {label} ({numberFormatter.format(count)})
            </Subtitle>
            <div className={clsx(styles.icon, isOpen && styles.isOpen)}>
              <Icon name="arrow_drop_down" />
            </div>
          </Box>
        </UnstyledButton>
        {children}
      </Box>
    </Box>
  );
};

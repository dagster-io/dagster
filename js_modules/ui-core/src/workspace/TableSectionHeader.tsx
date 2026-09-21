import {Box, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';

import styles from './css/TableSectionHeader.module.css';

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
    <button
      className={clsx(styles.sectionHeaderButton, !expanded && styles.collapsed)}
      onClick={onClick}
    >
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
    </button>
  );
};

import {Box, Colors, Icon} from '@dagster-io/ui-components';

import styles from './css/JobGroupSectionHeader.module.css';
import {TableSectionHeader, TableSectionHeaderProps} from '../workspace/TableSectionHeader';

const INDENT_PER_LEVEL = 16;

interface Props extends TableSectionHeaderProps {
  /** The last segment of the group name, e.g. `maintenance` for `operational/maintenance`. */
  groupName: string;
  /** Nesting level, where top-level groups are 0. */
  depth: number;
}

export const JobGroupSectionHeader = (props: Props) => {
  const {groupName, depth, ...rest} = props;
  return (
    <TableSectionHeader {...rest}>
      <Box
        flex={{alignItems: 'center', gap: 8}}
        padding={{left: 24}}
        style={{marginLeft: depth * INDENT_PER_LEVEL}}
      >
        <Icon name="asset_group" color={Colors.accentGray()} />
        <span className={styles.groupName}>{groupName}</span>
      </Box>
    </TableSectionHeader>
  );
};

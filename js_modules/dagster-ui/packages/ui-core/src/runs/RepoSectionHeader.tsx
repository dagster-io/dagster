import {Box, Colors, Icon} from '@dagster-io/ui-components';

import {TableSectionHeader, TableSectionHeaderProps} from '../workspace/TableSectionHeader';
import {DUNDER_REPO_NAME} from '../workspace/buildRepoAddress';
import styles from './RepoSectionHeader.module.css';

interface Props extends TableSectionHeaderProps {
  repoName: string;
  repoLocation: string;
  showLocation: boolean;
}

export const RepoSectionHeader = (props: Props) => {
  const {repoName, repoLocation, showLocation, ...rest} = props;
  const isDunderRepoName = repoName === DUNDER_REPO_NAME;
  return (
    <TableSectionHeader {...rest}>
      <Box flex={{alignItems: 'center', gap: 8}}>
        <Icon name="folder" color={Colors.accentGray()} />
        <div>
          <span className={styles.repoName}>{isDunderRepoName ? repoLocation : repoName}</span>
          {showLocation && !isDunderRepoName ? (
            <span className={styles.repoLocation}>{`@${repoLocation}`}</span>
          ) : null}
        </div>
      </Box>
    </TableSectionHeader>
  );
};

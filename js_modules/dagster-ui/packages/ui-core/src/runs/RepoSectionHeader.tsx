import {Box, Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {TableSectionHeader, TableSectionHeaderProps} from '../workspace/TableSectionHeader';
import {DUNDER_REPO_NAME} from '../workspace/buildRepoAddress';

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
          <RepoName>{isDunderRepoName ? repoLocation : repoName}</RepoName>
          {showLocation && !isDunderRepoName ? (
            <RepoLocation>{`@${repoLocation}`}</RepoLocation>
          ) : null}
        </div>
      </Box>
    </TableSectionHeader>
  );
};

const RepoName = styled.span`
  font-weight: 600;
`;

const RepoLocation = styled.span`
  font-weight: 400;
  color: ${Colors.textLighter()};
`;

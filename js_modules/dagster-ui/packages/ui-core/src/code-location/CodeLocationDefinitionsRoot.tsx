import {Box} from '@dagster-io/ui-components';
import {CodeLocationTabs} from 'shared/code-location/CodeLocationTabs.oss';

import {CodeLocationDefinitionsMain} from './CodeLocationDefinitionsMain';
import {CodeLocationDefinitionsNav} from './CodeLocationDefinitionsNav';
import {CodeLocationPageHeader} from './CodeLocationPageHeader';
import {WorkspaceRepositoryFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  repository: WorkspaceRepositoryFragment;
}

export const CodeLocationDefinitionsRoot = (props: Props) => {
  const {repoAddress, repository} = props;
  return (
    <Box style={{height: '100%', overflow: 'hidden'}} flex={{direction: 'column'}}>
      <CodeLocationPageHeader repoAddress={repoAddress} />
      <Box padding={{horizontal: 24}} border="bottom">
        <CodeLocationTabs selectedTab="definitions" repoAddress={repoAddress} />
      </Box>
      <Box style={{overflow: 'hidden'}} flex={{direction: 'row', grow: 1}}>
        <Box
          style={{flex: '0 0 292px', overflowY: 'auto'}}
          padding={{vertical: 16, horizontal: 12}}
          border="right"
        >
          <CodeLocationDefinitionsNav repoAddress={repoAddress} repository={repository} />
        </Box>
        <Box
          flex={{direction: 'column', alignItems: 'stretch'}}
          style={{flex: 1, overflow: 'hidden'}}
        >
          <CodeLocationDefinitionsMain repoAddress={repoAddress} repository={repository} />
        </Box>
      </Box>
    </Box>
  );
};

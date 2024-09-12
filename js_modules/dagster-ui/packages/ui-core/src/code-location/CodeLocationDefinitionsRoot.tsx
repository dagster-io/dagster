import {Box} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Redirect} from 'react-router-dom';
import {CodeLocationPageHeader} from 'shared/code-location/CodeLocationPageHeader.oss';
import {CodeLocationTabs} from 'shared/code-location/CodeLocationTabs.oss';

import {CodeLocationDefinitionsMain} from './CodeLocationDefinitionsMain';
import {CodeLocationDefinitionsNav} from './CodeLocationDefinitionsNav';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {WorkspaceRepositoryFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  repository: WorkspaceRepositoryFragment;
}

export const CodeLocationDefinitionsRoot = (props: Props) => {
  const {repoAddress, repository} = props;
  const {locationEntries, loading} = useContext(WorkspaceContext);
  const locationEntry = locationEntries.find((entry) => entry.name === repoAddress.location);

  if (!locationEntry) {
    if (!loading) {
      return <Redirect to="/deployment/locations" />;
    }
    return <div />;
  }

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

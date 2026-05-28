import {Box} from '@dagster-io/ui-components';
import {CodeLocationPageHeader} from '@shared/code-location/CodeLocationPageHeader';
import {CodeLocationTabs} from '@shared/code-location/CodeLocationTabs';
import {useContext} from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {CodeLocationComponentsCatalogSubtab} from './CodeLocationComponentsCatalogSubtab';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const CodeLocationComponentsRoot = ({repoAddress}: Props) => {
  const {locationEntries, loadingNonAssets: loading} = useContext(WorkspaceContext);
  const locationEntry = locationEntries.find((entry) => entry.name === repoAddress.location);

  const params = useParams<{
    packageName?: string;
    componentName?: string;
  }>();

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
        <CodeLocationTabs
          selectedTab="components"
          repoAddress={repoAddress}
          locationEntry={locationEntry}
        />
      </Box>
      <Box flex={{direction: 'column'}} style={{flex: 1, overflow: 'auto'}}>
        <CodeLocationComponentsCatalogSubtab
          repoAddress={repoAddress}
          packageName={params.packageName}
          componentName={params.componentName}
        />
      </Box>
    </Box>
  );
};

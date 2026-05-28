import {Box, Button, ButtonGroup, Icon} from '@dagster-io/ui-components';
import {CodeLocationPageHeader} from '@shared/code-location/CodeLocationPageHeader';
import {CodeLocationTabs} from '@shared/code-location/CodeLocationTabs';
import {useContext, useState} from 'react';
import {Redirect, useHistory, useLocation, useParams} from 'react-router-dom';

import {CodeLocationComponentInstancesSubtab} from './CodeLocationComponentInstancesSubtab';
import {CodeLocationComponentsCatalogSubtab} from './CodeLocationComponentsCatalogSubtab';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
}

export type ComponentsSubTab = 'instances' | 'library';

export const CodeLocationComponentsRoot = ({repoAddress}: Props) => {
  const {locationEntries, loadingNonAssets: loading} = useContext(WorkspaceContext);
  const locationEntry = locationEntries.find((entry) => entry.name === repoAddress.location);

  const params = useParams<{
    packageName?: string;
    componentName?: string;
  }>();

  // Routes:
  //   ``/components``                        -> instances (default)
  //   ``/components/library[/packages/...]`` -> library (component-type registry)
  const location = useLocation();
  const subTab: ComponentsSubTab = location.pathname.includes('/components/library')
    ? 'library'
    : 'instances';

  const history = useHistory();

  const [isAddOpen, setIsAddOpen] = useState(false);

  if (!locationEntry) {
    if (!loading) {
      return <Redirect to="/deployment/locations" />;
    }
    return <div />;
  }

  const renderSubTab = () => {
    if (subTab === 'library') {
      return (
        <CodeLocationComponentsCatalogSubtab
          repoAddress={repoAddress}
          packageName={params.packageName}
          componentName={params.componentName}
        />
      );
    }
    return (
      <CodeLocationComponentInstancesSubtab
        repoAddress={repoAddress}
        isAddOpen={isAddOpen}
        setIsAddOpen={setIsAddOpen}
      />
    );
  };

  const onSubTabClick = (id: ComponentsSubTab) => {
    history.push(
      workspacePathFromAddress(
        repoAddress,
        id === 'library' ? '/components/library' : '/components',
      ),
    );
  };

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
      <Box
        padding={{horizontal: 24, vertical: 12}}
        border="bottom"
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
      >
        <ButtonGroup<ComponentsSubTab>
          activeItems={new Set([subTab])}
          buttons={[
            {id: 'library', label: 'Library'},
            {id: 'instances', label: 'Instances'},
          ]}
          onClick={onSubTabClick}
        />
        {subTab === 'instances' ? (
          <Button
            intent="primary"
            icon={<Icon name="add_circle" />}
            onClick={() => setIsAddOpen(true)}
          >
            Add
          </Button>
        ) : null}
      </Box>
      <Box flex={{direction: 'column'}} style={{flex: 1, overflow: 'auto'}}>
        {renderSubTab()}
      </Box>
    </Box>
  );
};

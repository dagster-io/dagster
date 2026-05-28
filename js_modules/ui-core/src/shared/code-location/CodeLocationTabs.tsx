import {Box, Tab, Tabs, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {findRepositoryInLocation} from '../../code-location/findRepositoryInLocation';
import {TabLink} from '../../ui/TabLink';
import {WorkspaceLocationNodeFragment} from '../../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';

export type CodeLocationTabType = 'overview' | 'definitions' | 'components';

interface Props {
  repoAddress: RepoAddress;
  selectedTab: CodeLocationTabType;
  locationEntry: WorkspaceLocationNodeFragment | null;
}

export const CodeLocationTabs = (props: Props) => {
  const {repoAddress, selectedTab, locationEntry} = props;

  const repository = useMemo(
    () => findRepositoryInLocation(locationEntry, repoAddress),
    [locationEntry, repoAddress],
  );

  return (
    <Tabs selectedTabId={selectedTab}>
      <TabLink id="overview" title="Overview" to={workspacePathFromAddress(repoAddress, '/')} />
      {repository ? (
        <TabLink
          id="definitions"
          title="Definitions"
          to={workspacePathFromAddress(repoAddress, '/definitions')}
        />
      ) : (
        <Tab id="definitions" title="Definitions" disabled />
      )}
      <TabLink
        id="components"
        title={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <span>Components</span>
            <Tag>
              <span style={{fontWeight: 'normal'}}>Beta</span>
            </Tag>
          </Box>
        }
        to={workspacePathFromAddress(repoAddress, '/components')}
      />
    </Tabs>
  );
};

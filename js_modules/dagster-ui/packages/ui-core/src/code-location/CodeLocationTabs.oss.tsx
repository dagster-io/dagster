import {Tabs} from '@dagster-io/ui-components';

import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export type CodeLocationTabType = 'overview' | 'definitions';

interface Props {
  repoAddress: RepoAddress;
  selectedTab: CodeLocationTabType;
}

export const CodeLocationTabs = (props: Props) => {
  const {repoAddress, selectedTab} = props;
  return (
    <Tabs selectedTabId={selectedTab}>
      <TabLink id="overview" title="Overview" to={workspacePathFromAddress(repoAddress, '/')} />
      <TabLink
        id="definitions"
        title="Definitions"
        to={workspacePathFromAddress(repoAddress, '/definitions')}
      />
    </Tabs>
  );
};

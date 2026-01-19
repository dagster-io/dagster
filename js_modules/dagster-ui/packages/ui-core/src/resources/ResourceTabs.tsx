import {Box, Tabs, Tag} from '@dagster-io/ui-components';
import {useRouteMatch} from 'react-router-dom';

import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const titles: {[key: string]: string} = {
  configuration: '配置',
  uses: '使用',
};

export const ResourceTabs = (props: {
  repoAddress: RepoAddress;
  resourceName: string;
  numUses: number;
}) => {
  const {repoAddress, resourceName, numUses} = props;

  const match = useRouteMatch<{tab?: string; selector: string}>([
    '/locations/:repoPath/resources/:name/:tab?',
  ]);

  const active = (match?.params.tab && titles[match?.params.tab]) || '配置';

  return (
    <>
      <Tabs size="large" selectedTabId={active}>
        <TabLink
          key="configuration"
          id="配置"
          title="配置"
          to={workspacePathFromAddress(repoAddress, `/resources/${resourceName}`)}
        />
        <TabLink
          key="uses"
          id="使用"
          title={
            <Box flex={{gap: 4, alignItems: 'center'}}>
              使用
              <Tag intent="none">{numUses}</Tag>
            </Box>
          }
          to={workspacePathFromAddress(repoAddress, `/resources/${resourceName}/uses`)}
        />
      </Tabs>
    </>
  );
};

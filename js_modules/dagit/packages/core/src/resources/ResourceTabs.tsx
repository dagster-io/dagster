import {Box, Tabs, Tag} from '@dagster-io/ui';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const titles: {[key: string]: string} = {
  configuration: 'Configuration',
  uses: 'Uses',
};

export const ResourceTabs: React.FC<{
  repoAddress: RepoAddress;
  resourceName: string;
  numParentResources: number;
}> = (props) => {
  const {repoAddress, resourceName, numParentResources} = props;

  const match = useRouteMatch<{tab?: string; selector: string}>([
    '/locations/:repoPath/resources/:name/:tab?',
  ]);

  const active = (match?.params.tab && titles[match?.params.tab]) || 'Configuration';

  return (
    <>
      <Tabs size="large" selectedTabId={active}>
        <TabLink
          key="configuration"
          id="Configuration"
          title="Configuration"
          to={workspacePathFromAddress(repoAddress, `/resources/${resourceName}`)}
        />
        <TabLink
          key="uses"
          id="Uses"
          title={
            <Box flex={{gap: 4, alignItems: 'center'}}>
              Uses
              <Tag intent="none" minimal={true}>
                {numParentResources}
              </Tag>
            </Box>
          }
          to={workspacePathFromAddress(repoAddress, `/resources/${resourceName}/uses`)}
        />
      </Tabs>
    </>
  );
};

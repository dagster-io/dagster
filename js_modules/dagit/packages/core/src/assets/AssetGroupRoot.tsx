import {Box, Heading, Page, PageHeader, Tabs, Tag} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepositoryLink} from '../nav/RepositoryLink';
import {explorerPathFromString, explorerPathToString} from '../pipelines/PipelinePathUtils';
import {TabLink} from '../ui/TabLink';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetsCatalogTable} from './AssetsCatalogTable';

export const AssetGroupRoot: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const params = useParams();
  const history = useHistory();
  const explorerPath = explorerPathFromString(params[0]);
  const {pipelineName: groupName, opNames: prefixPath} = explorerPath;

  useDocumentTitle(`Asset Group: ${groupName}`);

  const [tab = 'lineage'] = useQueryPersistedState<'lineage' | 'list'>({queryKey: 'tab'});
  const groupSelector = React.useMemo(
    () => ({
      groupName,
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
    }),
    [groupName, repoAddress],
  );

  return (
    <Page style={{display: 'flex', flexDirection: 'column', paddingBottom: 0}}>
      <PageHeader
        title={<Heading>{groupName}</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
        tags={
          <Tag icon="asset_group">
            Asset Group in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
        tabs={
          <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
            <Tabs selectedTabId={tab}>
              <TabLink
                id="lineage"
                title="Lineage"
                to={workspacePathFromAddress(repoAddress, `/asset-groups/${groupName}?tab=lineage`)}
              />
              <TabLink
                id="list"
                title="List"
                to={workspacePathFromAddress(repoAddress, `/asset-groups/${groupName}?tab=list`)}
              />
            </Tabs>
          </Box>
        }
      />
      {tab === 'lineage' ? (
        <AssetGraphExplorer
          fetchOptions={{groupSelector}}
          options={{preferAssetRendering: true, explodeComposites: true}}
          explorerPath={explorerPath}
          onChangeExplorerPath={(path, mode) => {
            history[mode](
              workspacePathFromAddress(repoAddress, `/asset-groups/${explorerPathToString(path)}`),
            );
          }}
        />
      ) : (
        <AssetsCatalogTable prefixPath={prefixPath.filter(Boolean)} groupSelector={groupSelector} />
      )}
    </Page>
  );
};

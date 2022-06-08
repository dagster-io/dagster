import {Box, Heading, Page, PageHeader, Tabs, Tag} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepositoryLink} from '../nav/RepositoryLink';
import {explorerPathFromString, explorerPathToString} from '../pipelines/PipelinePathUtils';
import {TabLink} from '../ui/TabLink';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetsCatalogTable} from './AssetsCatalogTable';

interface AssetGroupRootParams {
  groupName: string;
  prefixPath: string;
  0: string;
}

export const AssetGroupRoot: React.FC<{repoAddress: RepoAddress; tab: 'lineage' | 'list'}> = ({
  repoAddress,
  tab,
}) => {
  const {groupName, 0: path} = useParams<AssetGroupRootParams>();
  const history = useHistory();

  useDocumentTitle(`Asset Group: ${groupName}`);

  const groupPath = workspacePathFromAddress(repoAddress, `/asset-groups/${groupName}`);
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
        right={
          <div style={{marginBottom: -8}}>
            <ReloadAllButton label="Reload definitions" />
          </div>
        }
        tags={
          <Tag icon="asset_group">
            Asset Group in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
        tabs={
          <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
            <Tabs selectedTabId={tab}>
              <TabLink id="lineage" title="Lineage" to={`${groupPath}/lineage`} />
              <TabLink id="list" title="List" to={`${groupPath}/list`} />
            </Tabs>
          </Box>
        }
      />
      {tab === 'lineage' ? (
        <AssetGraphExplorer
          fetchOptions={{groupSelector}}
          options={{preferAssetRendering: true, explodeComposites: true}}
          explorerPath={explorerPathFromString(path || 'lineage/')}
          onChangeExplorerPath={(path, mode) => {
            history[mode](`${groupPath}/${explorerPathToString(path)}`);
          }}
        />
      ) : (
        <AssetsCatalogTable
          groupSelector={groupSelector}
          prefixPath={path.split('/').map(decodeURIComponent).filter(Boolean)}
          setPrefixPath={(prefixPath) =>
            history.push(`${groupPath}/list/${prefixPath.map(encodeURIComponent).join('/')}`)
          }
        />
      )}
    </Page>
  );
};

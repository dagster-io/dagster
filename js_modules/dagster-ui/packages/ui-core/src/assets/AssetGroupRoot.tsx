import {Box, Heading, Page, PageHeader, Tabs, Tag} from '@dagster-io/ui-components';
import React, {useCallback, useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {AssetGlobalLineageLink} from 'shared/assets/AssetPageHeader.oss';

import {AssetsCatalogTable} from './AssetsCatalogTable';
import {useAutoMaterializeSensorFlag} from './AutoMaterializeSensorFlag';
import {AutomaterializeDaemonStatusTag} from './AutomaterializeDaemonStatusTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  AssetGroupMetadataQuery,
  AssetGroupMetadataQueryVariables,
} from './types/AssetGroupRoot.types';
import {gql, useQuery} from '../apollo-client';
import {useTrackPageView} from '../app/analytics';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphViewType} from '../asset-graph/Utils';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {AssetGroupSelector} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepositoryLink} from '../nav/RepositoryLink';
import {
  ExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from '../pipelines/PipelinePathUtils';
import {TabLink} from '../ui/TabLink';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface AssetGroupRootParams {
  groupName: string;
  prefixPath: string;
  0: string;
}

export const AssetGroupRoot = ({
  repoAddress,
  tab,
}: {
  repoAddress: RepoAddress;
  tab: 'lineage' | 'list';
}) => {
  useTrackPageView();

  const {groupName, 0: path} = useParams<AssetGroupRootParams>();
  const history = useHistory();

  useDocumentTitle(`Asset Group: ${groupName}`);

  const groupPath = workspacePathFromAddress(repoAddress, `/asset-groups/${groupName}`);
  const groupSelector = useMemo(
    () => ({
      groupName,
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
    }),
    [groupName, repoAddress],
  );

  const onChangeExplorerPath = useCallback(
    (path: ExplorerPath, mode: 'push' | 'replace') => {
      history[mode]({
        pathname: `${groupPath}/${explorerPathToString(path)}`,
        search: history.location.search,
      });
    },
    [groupPath, history],
  );

  const onNavigateToSourceAssetNode = useCallback(
    (e: Pick<React.MouseEvent<any>, 'metaKey'>, node: AssetLocation) => {
      let path;
      if (node.groupName && node.repoAddress) {
        path = workspacePathFromAddress(
          node.repoAddress,
          `/asset-groups/${node.groupName}/lineage/${node.assetKey.path
            .map(encodeURIComponent)
            .join('/')}`,
        );
      } else {
        path = assetDetailsPathForKey(node.assetKey, {view: 'definition'});
      }
      if (e.metaKey) {
        window.open(path, '_blank');
      } else {
        history.push(path);
      }
    },
    [history],
  );

  const fetchOptions = React.useMemo(() => ({groupSelector}), [groupSelector]);

  const lineageOptions = React.useMemo(
    () => ({preferAssetRendering: true, explodeComposites: true}),
    [],
  );

  return (
    <Page style={{display: 'flex', flexDirection: 'column', paddingBottom: 0}}>
      <PageHeader
        title={<Heading>{groupName}</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
        tags={<AssetGroupTags groupSelector={groupSelector} repoAddress={repoAddress} />}
        tabs={
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
            margin={{right: 4}}
          >
            <Tabs selectedTabId={tab}>
              <TabLink id="lineage" title="Lineage" to={`${groupPath}/lineage`} />
              <TabLink id="list" title="List" to={`${groupPath}/list`} />
            </Tabs>
            <AssetGlobalLineageLink />
          </Box>
        }
      />
      {tab === 'lineage' ? (
        <AssetGraphExplorer
          fetchOptions={fetchOptions}
          options={lineageOptions}
          explorerPath={explorerPathFromString(path || 'lineage/')}
          onChangeExplorerPath={onChangeExplorerPath}
          onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
          viewType={AssetGraphViewType.GROUP}
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

export const ASSET_GROUP_METADATA_QUERY = gql`
  query AssetGroupMetadataQuery($selector: AssetGroupSelector!) {
    assetNodes(group: $selector) {
      id
      autoMaterializePolicy {
        __typename
      }
    }
  }
`;

export const AssetGroupTags = ({
  repoAddress,
  groupSelector,
}: {
  groupSelector: AssetGroupSelector;
  repoAddress: RepoAddress;
}) => {
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  const queryResult = useQuery<AssetGroupMetadataQuery, AssetGroupMetadataQueryVariables>(
    ASSET_GROUP_METADATA_QUERY,
    {variables: {selector: groupSelector}},
  );
  const {data} = queryResult;

  const sensorTag = () => {
    const assetNodes = data?.assetNodes;
    if (!assetNodes || assetNodes.length === 0) {
      return null;
    }

    if (
      automaterializeSensorsFlagState === 'has-global-amp' &&
      assetNodes.some((a) => !!a.autoMaterializePolicy)
    ) {
      return <AutomaterializeDaemonStatusTag />;
    }

    return null;
  };

  return (
    <>
      <Tag icon="asset_group">
        Asset Group in <RepositoryLink repoAddress={repoAddress} />
      </Tag>
      {sensorTag()}
    </>
  );
};

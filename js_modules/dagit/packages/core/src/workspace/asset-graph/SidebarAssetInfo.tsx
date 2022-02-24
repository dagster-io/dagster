import {gql, useQuery} from '@apollo/client';
import {Box, ColorsWIP, IconWIP, Spinner} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetEvents} from '../../assets/AssetEvents';
import {
  AssetMetadataTable,
  ASSET_NODE_OP_METADATA_FRAGMENT,
  metadataForAssetNode,
} from '../../assets/AssetMetadata';
import {PartitionHealthSummary, usePartitionHealthData} from '../../assets/PartitionHealthSummary';
import {AssetKey} from '../../assets/types';
import {DagsterTypeSummary} from '../../dagstertype/DagsterType';
import {DagsterTypeFragment} from '../../dagstertype/types/DagsterTypeFragment';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {pluginForMetadata} from '../../plugins';
import {buildRepoAddress} from '../buildRepoAddress';
import {RepoAddress} from '../types';

import {LiveDataForNode} from './Utils';
import {SidebarAssetFragment} from './types/SidebarAssetFragment';
import {SidebarAssetQuery} from './types/SidebarAssetQuery';

export const SidebarAssetInfo: React.FC<{
  assetKey: AssetKey;
  liveData: LiveDataForNode;
}> = ({assetKey, liveData}) => {
  const partitionHealthData = usePartitionHealthData([assetKey]);
  const {data} = useQuery<SidebarAssetQuery>(SIDEBAR_ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
    fetchPolicy: 'cache-and-network',
  });

  const {lastMaterialization} = liveData || {};
  const asset = data?.assetNodeOrError.__typename === 'AssetNode' ? data.assetNodeOrError : null;
  if (!asset) {
    return (
      <>
        <Header assetKey={assetKey} />
        <Box padding={{vertical: 64}}>
          <Spinner purpose="section" />
        </Box>
      </>
    );
  }

  const repoAddress = buildRepoAddress(asset.repository.name, asset.repository.location.name);
  const {assetMetadata, assetType} = metadataForAssetNode(asset);

  return (
    <>
      <Header assetKey={assetKey} opName={asset.op?.name} />

      {(asset.description || !(asset.description || assetType || assetMetadata)) && (
        <DescriptionSidebarSection asset={asset} repoAddress={repoAddress} />
      )}

      {assetMetadata.length > 0 && (
        <SidebarSection title="Metadata">
          <AssetMetadataTable assetMetadata={assetMetadata} />
        </SidebarSection>
      )}

      {assetType && <TypeSidebarSection assetType={assetType} />}

      {asset.partitionDefinition && (
        <SidebarSection title="Partitions">
          <Box padding={{vertical: 16, horizontal: 24}} flex={{direction: 'column', gap: 16}}>
            <p>{asset.partitionDefinition}</p>
            <PartitionHealthSummary assetKey={asset.assetKey} data={partitionHealthData} />
          </Box>
        </SidebarSection>
      )}

      <div style={{borderBottom: `2px solid ${ColorsWIP.Gray300}`}} />

      <AssetEvents
        assetKey={assetKey}
        assetLastMaterializedAt={lastMaterialization?.timestamp}
        assetHasDefinedPartitions={!!asset.partitionDefinition}
        asSidebarSection
        liveData={liveData}
        paramsTimeWindowOnly={false}
        params={{}}
        setParams={() => {}}
      />
    </>
  );
};

const DescriptionSidebarSection: React.FC<{
  asset: SidebarAssetFragment;
  repoAddress: RepoAddress;
}> = ({asset, repoAddress}) => {
  const Plugin = asset.op?.metadata && pluginForMetadata(asset.op.metadata);

  return (
    <SidebarSection title="Description">
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Description description={asset.description || 'No description provided.'} />
      </Box>
      {asset.op && Plugin && Plugin.SidebarComponent && (
        <Plugin.SidebarComponent definition={asset.op} repoAddress={repoAddress} />
      )}
    </SidebarSection>
  );
};

const TypeSidebarSection: React.FC<{
  assetType: DagsterTypeFragment;
}> = ({assetType}) => {
  return (
    <SidebarSection title="Type">
      <DagsterTypeSummary type={assetType} />
    </SidebarSection>
  );
};

const Header: React.FC<{assetKey: AssetKey; opName?: string}> = ({assetKey, opName}) => {
  const displayName = displayNameForAssetKey(assetKey);

  return (
    <Box flex={{gap: 4, direction: 'column'}} margin={{left: 24, right: 12, vertical: 16}}>
      <SidebarTitle
        style={{
          marginBottom: 0,
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
        }}
      >
        <Box>{displayName}</Box>
        {displayName !== opName ? (
          <Box style={{opacity: 0.5}} flex={{gap: 6, alignItems: 'center'}}>
            <IconWIP name="op" size={16} />
            {opName}
          </Box>
        ) : undefined}
      </SidebarTitle>
      <AssetCatalogLink to={`/instance/assets/${assetKey.path.join('/')}`}>
        {'View in Asset Catalog '}
        <IconWIP name="open_in_new" color={ColorsWIP.Link} />
      </AssetCatalogLink>
    </Box>
  );
};
const AssetCatalogLink = styled(Link)`
  display: flex;
  gap: 5px;
  padding: 6px;
  margin: -6px;
  align-items: center;
  white-space: nowrap;
`;

export const SIDEBAR_ASSET_FRAGMENT = gql`
  fragment SidebarAssetFragment on AssetNode {
    id
    description
    partitionDefinition
    assetKey {
      path
    }
    op {
      name
      description
      metadata {
        key
        value
      }
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }

    ...AssetNodeOpMetadataFragment
  }
  ${ASSET_NODE_OP_METADATA_FRAGMENT}
`;

const SIDEBAR_ASSET_QUERY = gql`
  query SidebarAssetQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      __typename
      ... on AssetNode {
        id
        ...SidebarAssetFragment
      }
    }
  }
  ${SIDEBAR_ASSET_FRAGMENT}
`;

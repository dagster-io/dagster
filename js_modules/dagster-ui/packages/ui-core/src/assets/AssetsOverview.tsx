import {useQuery} from '@apollo/client';
import {Box, Colors, Heading, Icon, Page, Spinner, TextInput} from '@dagster-io/ui-components';
import {Link, useParams} from 'react-router-dom';
import styled from 'styled-components';

import {AssetGlobalLineageButton, AssetPageHeader} from './AssetPageHeader';
import {ASSET_CATALOG_TABLE_QUERY} from './AssetsCatalogTable';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from './types/AssetsCatalogTable.types';
import {useTrackPageView} from '../app/analytics';
import {TagIcon} from '../graph/OpTags';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {repoAddressAsHumanString, repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const ViewAllAssetsLink = () => (
  <Link to="/assets">
    <Box flex={{gap: 4}}>View all</Box>
  </Link>
);

type AssetCountsResult = {
  countsByOwner: Record<string, number>;
  countsByComputeKind: Record<string, number>;
  countPerAssetGroup: CountPerGroupName[];
  countPerCodeLocation: CountPerCodeLocation[];
};

type GroupMetadata = {
  groupName: string;
  repositoryLocationName: string;
  repositoryName: string;
};

type CountPerGroupName = {
  assetCount: number;
  groupMetadata: GroupMetadata;
};

type CountPerCodeLocation = {
  repoAddress: RepoAddress;
  assetCount: number;
};

function buildAssetCountBySection(assets: AssetTableFragment[]): AssetCountsResult {
  const assetCountByOwner: Record<string, number> = {};
  const assetCountByComputeKind: Record<string, number> = {};
  const assetCountByGroup: Record<string, number> = {};
  const assetCountByCodeLocation: Record<string, number> = {};

  assets.forEach((asset) => {
    if (asset.definition) {
      asset.definition.owners.forEach((owner) => {
        const ownerKey = owner.__typename === 'UserAssetOwner' ? owner.email : owner.team;
        assetCountByOwner[ownerKey] = (assetCountByOwner[ownerKey] || 0) + 1;
      });

      const computeKind = asset.definition.computeKind;
      if (computeKind) {
        assetCountByComputeKind[computeKind] = (assetCountByComputeKind[computeKind] || 0) + 1;
      }

      const groupName = asset.definition.groupName;
      const locationName = asset.definition.repository.location.name;
      const repositoryName = asset.definition.repository.name;

      if (groupName) {
        const metadata: GroupMetadata = {
          groupName,
          repositoryLocationName: locationName,
          repositoryName,
        };
        const groupIdentifier = JSON.stringify(metadata);
        assetCountByGroup[groupIdentifier] = (assetCountByGroup[groupIdentifier] || 0) + 1;
      }

      const stringifiedCodeLocation = JSON.stringify({
        name: repositoryName,
        location: locationName,
      });
      assetCountByCodeLocation[stringifiedCodeLocation] =
        (assetCountByCodeLocation[stringifiedCodeLocation] || 0) + 1;
    }
  });

  const countPerAssetGroup: CountPerGroupName[] = [];
  Object.entries(assetCountByGroup).forEach(([groupIdentifier, count]) => {
    const metadata: GroupMetadata = JSON.parse(groupIdentifier);
    countPerAssetGroup.push({
      assetCount: count,
      groupMetadata: metadata,
    });
  });

  return {
    countsByOwner: assetCountByOwner,
    countsByComputeKind: assetCountByComputeKind,
    countPerAssetGroup,
    countPerCodeLocation: Object.entries(assetCountByCodeLocation).reduce(
      (a, [stringifiedRepoLocation, count]) =>
        a.concat({repoAddress: JSON.parse(stringifiedRepoLocation), assetCount: count}),
      [] as CountPerCodeLocation[],
    ),
  };
}

interface AssetOverviewCategoryProps {
  children: React.ReactNode;
  assetsCount: number;
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) {
    return 'Good morning';
  } else if (hour < 18) {
    return 'Good afternoon';
  } else {
    return 'Good evening';
  }
}

const CountForAssetType = ({children, assetsCount}: AssetOverviewCategoryProps) => {
  return (
    <Box
      flex={{direction: 'row', justifyContent: 'space-between'}}
      style={{width: 'calc(33% - 16px)'}}
    >
      <Box>{children}</Box>
      <Box>
        <AssetCount>{assetsCount} assets</AssetCount>
      </Box>
    </Box>
  );
};

const SectionHeader = ({sectionName}: {sectionName: string}) => {
  return (
    <Box
      flex={{alignItems: 'center', justifyContent: 'space-between'}}
      padding={{horizontal: 24, vertical: 8}}
      style={{
        borderBottom: `1px solid ${Colors.backgroundGray()}`,
        borderTop: `1px solid ${Colors.backgroundGray()}`,
      }}
    >
      <SectionName>{sectionName}</SectionName>
    </Box>
  );
};

const SectionBody = ({children}: {children: React.ReactNode}) => {
  return (
    <Box
      padding={{horizontal: 24, vertical: 16}}
      flex={{wrap: 'wrap'}}
      style={{rowGap: '14px', columnGap: '24px'}}
    >
      {children}
    </Box>
  );
};

const LinkToAssetGraphGroup = (groupMetadata: GroupMetadata) => {
  return `/asset-groups?groups=[${encodeURIComponent(JSON.stringify(groupMetadata))}]`;
};

const LinkToAssetGraphComputeKind = (computeKind: string) => {
  return `/asset-groups?computeKindTags=${encodeURIComponent(JSON.stringify([computeKind]))}`;
};

const LinkToCodeLocation = (repoAddress: RepoAddress) => {
  return `/locations/${repoAddressAsURLString(repoAddress)}/assets`;
};

export const AssetsOverview = ({viewerName}: {viewerName?: string}) => {
  useTrackPageView();

  const params = useParams();
  const currentPath: string[] = ((params as any)['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  useDocumentTitle('Assets');

  const assetsQuery = useQuery<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>(
    ASSET_CATALOG_TABLE_QUERY,
    {
      notifyOnNetworkStatusChange: true,
    },
  );
  const assetCountBySection = buildAssetCountBySection(
    assetsQuery.data?.assetsOrError.__typename === 'AssetConnection'
      ? assetsQuery.data.assetsOrError.nodes
      : [],
  );
  const {UserDisplay} = useLaunchPadHooks();

  if (assetsQuery.loading) {
    return (
      <Page>
        <AssetPageHeader assetKey={{path: currentPath}} />
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading assets…</div>
          </Box>
        </Box>
      </Page>
    );
  }

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <AssetPageHeader
        assetKey={{path: currentPath}}
        right={
          <Box flex={{gap: 12, alignItems: 'center'}}>
            <ReloadAllButton label="Reload definitions" />
          </Box>
        }
      />
      <Box
        padding={64}
        flex={{justifyContent: 'center', alignItems: 'center'}}
        style={{overflowY: 'scroll'}}
      >
        <Box style={{width: '60%'}} flex={{direction: 'column', gap: 16}}>
          <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
            <Heading>
              {getGreeting()}
              {viewerName ? `, ${viewerName}` : ''}
            </Heading>
            <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
              <ViewAllAssetsLink />
              <AssetGlobalLineageButton />
            </Box>
          </Box>
          <TextInput />
        </Box>
      </Box>
      <Box flex={{direction: 'column'}}>
        {Object.keys(assetCountBySection.countsByOwner).length > 0 && (
          <>
            <SectionHeader sectionName="Owner" />
            <SectionBody>
              {Object.entries(assetCountBySection.countsByOwner).map(([label, count], idx) => (
                <CountForAssetType key={idx} assetsCount={count}>
                  <UserDisplay key={idx} email={label} size="normal" />
                </CountForAssetType>
              ))}
            </SectionBody>
          </>
        )}
        {Object.keys(assetCountBySection.countsByComputeKind).length > 0 && (
          <>
            <SectionHeader sectionName="Compute kind" />
            <SectionBody>
              {Object.entries(assetCountBySection.countsByComputeKind).map(
                ([label, count], idx) => (
                  <CountForAssetType key={idx} assetsCount={count}>
                    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                      <TagIcon tag_label={label} />
                      <Link to={LinkToAssetGraphComputeKind(label)}>{label}</Link>
                    </Box>
                  </CountForAssetType>
                ),
              )}
            </SectionBody>
          </>
        )}
        {assetCountBySection.countPerAssetGroup.length > 0 && (
          <>
            <SectionHeader sectionName="Asset groups" />
            <SectionBody>
              {assetCountBySection.countPerAssetGroup.map(
                (assetGroupCount: CountPerGroupName, idx) => (
                  <CountForAssetType key={idx} assetsCount={assetGroupCount.assetCount}>
                    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                      <Icon name="asset_group" />
                      <Link to={LinkToAssetGraphGroup(assetGroupCount.groupMetadata)}>
                        {assetGroupCount.groupMetadata.groupName}
                      </Link>
                      <span style={{color: Colors.textLighter()}}>
                        {assetGroupCount.groupMetadata.repositoryLocationName}
                      </span>
                    </Box>
                  </CountForAssetType>
                ),
              )}
            </SectionBody>
          </>
        )}
        {assetCountBySection.countPerCodeLocation.length > 0 && (
          <>
            <SectionHeader sectionName="Code locations" />
            <SectionBody>
              {assetCountBySection.countPerCodeLocation.map((countPerCodeLocation, idx) => (
                <CountForAssetType key={idx} assetsCount={countPerCodeLocation.assetCount}>
                  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                    <Icon name="folder" />
                    <Link to={LinkToCodeLocation(countPerCodeLocation.repoAddress)}>
                      {repoAddressAsHumanString(countPerCodeLocation.repoAddress)}
                    </Link>
                  </Box>
                </CountForAssetType>
              ))}
            </SectionBody>
          </>
        )}
      </Box>
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsOverview;

const SectionName = styled.span`
  font-weight: 600;
  color: ${Colors.textLight()};
  font-size: 12px;
`;

const AssetCount = styled.span`
  color: ${Colors.textLight()};
  font-size: 14px;
`;

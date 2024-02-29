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

const ViewAllAssetsLink = () => (
  <Link to="/assets">
    <Box flex={{gap: 4}}>View all</Box>
  </Link>
);

const SECTIONS = ['Recently visited', 'Owner', 'Compute kind', 'Asset groups', 'Code locations'];

type AssetCategoryAndCount = {
  label: string;
  codeLocationName: string;
  assetCount: number;
};

function buildAssetCountBySection(assets: AssetTableFragment[]): Record<string, any> {
  const assetCountByOwner: Record<string, number> = {};
  const assetCountByComputeKind: Record<string, number> = {};
  const countByGroupByCodeLocation: Record<string, Record<string, number>> = {};
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

      if (groupName) {
        if (!countByGroupByCodeLocation[locationName]) {
          countByGroupByCodeLocation[locationName] = {};
        }
        countByGroupByCodeLocation[locationName]![groupName] =
          (countByGroupByCodeLocation[locationName]![groupName] || 0) + 1;
      }

      assetCountByCodeLocation[locationName] = (assetCountByCodeLocation[locationName] || 0) + 1;
    }
  });

  const countsPerAssetGroup: AssetCategoryAndCount[] = [];
  Object.keys(countByGroupByCodeLocation).forEach((locationName) => {
    Object.keys(countByGroupByCodeLocation[locationName]!).forEach((groupName) => {
      countsPerAssetGroup.push({
        label: groupName,
        codeLocationName: locationName,
        assetCount: countByGroupByCodeLocation[locationName]![groupName]!,
      });
    });
  });

  return {
    Owner: assetCountByOwner,
    'Compute kind': assetCountByComputeKind,
    'Asset groups': countsPerAssetGroup,
    'Code locations': assetCountByCodeLocation,
  };
}

interface AssetOverviewCategoryProps {
  children: React.ReactNode;
  assetsCount: number;
}

const AssetOverviewCategoryCount = ({children, assetsCount}: AssetOverviewCategoryProps) => {
  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between'}} style={assetCountEntry}>
      <Box>{children}</Box>
      <Box>
        <AssetCount>{assetsCount} assets</AssetCount>
      </Box>
    </Box>
  );
};

const IconBySection = ({section, label}: {section: string; label: string}) => {
  switch (section) {
    case 'Recently visited':
      return <Icon name="asset" />;
    case 'Owner':
      return null;
    case 'Compute kind':
      return <TagIcon tag_label={label} />;
    case 'Asset groups':
      return <Icon name="asset_group" />;
    case 'Code locations':
      return <Icon name="folder" />;
    default:
      return null;
  }
};

export const AssetsOverview = () => {
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
      <Box padding={64} flex={{justifyContent: 'center', alignItems: 'center'}}>
        <Box style={{width: '60%'}} flex={{direction: 'column', gap: 16}}>
          <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
            <Heading>Good morning, Name</Heading>
            <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
              <ViewAllAssetsLink />
              <AssetGlobalLineageButton />
            </Box>
          </Box>
          <TextInput />
        </Box>
      </Box>
      <Box flex={{direction: 'column'}}>
        {SECTIONS.map((section, idx) =>
          section in assetCountBySection && Object.keys(assetCountBySection[section]).length > 0 ? (
            <Box key={idx}>
              <Box
                flex={{alignItems: 'center', justifyContent: 'space-between'}}
                padding={{horizontal: 24, vertical: 8}}
                style={{
                  borderBottom: `1px solid ${Colors.backgroundGray()}`,
                  borderTop: `1px solid ${Colors.backgroundGray()}`,
                }}
              >
                <SectionName>{section}</SectionName>
              </Box>
              <Box
                padding={{horizontal: 24, vertical: 16}}
                flex={{wrap: 'wrap'}}
                style={{rowGap: '14px', columnGap: '24px'}}
              >
                {section === 'Asset groups'
                  ? assetCountBySection[section].map(
                      (assetGroupCount: AssetCategoryAndCount, idx) => {
                        console.log(assetGroupCount);
                        return (
                          <AssetOverviewCategoryCount
                            key={idx}
                            assetsCount={assetGroupCount.assetCount}
                          >
                            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                              <IconBySection section={section} label={assetGroupCount.label} />
                              <span>{assetGroupCount.label}</span>
                              <span style={{color: Colors.textLighter()}}>
                                {assetGroupCount.codeLocationName}
                              </span>
                            </Box>
                          </AssetOverviewCategoryCount>
                        );
                      },
                    )
                  : Object.entries(assetCountBySection[section]).map(([label, count], idx) => (
                      <AssetOverviewCategoryCount key={idx} assetsCount={count}>
                        {section === 'Owner' ? (
                          <UserDisplay key={idx} email={label} size="normal" />
                        ) : (
                          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                            <IconBySection section={section} label={label} />
                            <span>{label}</span>
                          </Box>
                        )}
                      </AssetOverviewCategoryCount>
                    ))}
              </Box>
            </Box>
          ) : null,
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
  // font-weight: 00;
  color: ${Colors.textLight()};
  font-size: 14px;
`;

const assetCountEntry: React.CSSProperties = {
  width: 'calc(33% - 16px)',
};

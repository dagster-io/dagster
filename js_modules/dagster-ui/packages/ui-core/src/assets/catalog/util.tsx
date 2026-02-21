import {BodySmall, Box, Colors, Icon, Popover, Spinner, ifPlural} from '@dagster-io/ui-components';
import {useCatalogViews} from '@shared/assets/catalog/useCatalogViews';
import {useMemo} from 'react';

import styles from './AssetSelectionSummaryTile.module.css';
import {assertUnreachable} from '../../app/Util';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {AssetHealthStatus} from '../../graphql/types';
import {
  linkToAssetTableWithAssetOwnerFilter,
  linkToAssetTableWithCrossCodeLocationGroupFilter,
  linkToAssetTableWithKindFilter,
  linkToAssetTableWithTagFilter,
  linkToCodeLocationInCatalog,
} from '../../search/links';
import {compactNumberFormatter} from '../../ui/formatters';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {statusToIconAndColor} from '../AssetHealthSummary';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export type ViewType =
  | ReturnType<typeof useCatalogViews>['privateViews'][number]
  | ReturnType<typeof useCatalogViews>['publicViews'][number];

type GroupedAssets = Record<string, {label: string; assets: AssetTableFragment[]; link: string}>;

export function getGroupedAssets(assets: AssetTableFragment[]) {
  return assets.reduce(
    (acc, asset) => {
      const {definition} = asset;
      if (!definition) {
        return acc;
      }
      const {owners, groupName, repository, tags, kinds} = definition;
      if (owners) {
        owners.forEach((owner) => {
          switch (owner.__typename) {
            case 'TeamAssetOwner':
              acc.owners[owner.team] = acc.owners[owner.team] || {
                assets: [],
                label: owner.team,
                link: linkToAssetTableWithAssetOwnerFilter(owner),
              };
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              acc.owners[owner.team]!.assets.push(asset);
              break;
            case 'UserAssetOwner':
              acc.owners[owner.email] = acc.owners[owner.email] || {
                assets: [],
                label: owner.email,
                link: linkToAssetTableWithAssetOwnerFilter(owner),
              };
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              acc.owners[owner.email]!.assets.push(asset);
              break;
            default:
              assertUnreachable(owner);
          }
        });
      }
      if (groupName) {
        acc.groupName[groupName] = acc.groupName[groupName] || {
          assets: [],
          label: groupName,
          link: linkToAssetTableWithCrossCodeLocationGroupFilter(groupName),
        };
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        acc.groupName[groupName]!.assets.push(asset);
      }
      if (repository) {
        const name = buildRepoPathForHuman(repository.name, repository.location.name);
        acc.repository[name] = acc.repository[name] || {
          assets: [],
          label: name,
          link: linkToCodeLocationInCatalog(repository.name, repository.location.name),
        };
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        acc.repository[name]!.assets.push(asset);
      }
      if (tags) {
        tags.forEach((tag) => {
          const stringValue = `${tag.key}${tag.value ? ': ' + tag.value : ''}`;
          acc.tags[stringValue] = acc.tags[stringValue] || {
            assets: [],
            label: stringValue,
            link: linkToAssetTableWithTagFilter(tag),
          };
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          acc.tags[stringValue]!.assets.push(asset);
        });
      }
      if (kinds) {
        kinds.forEach((kind) => {
          acc.kinds[kind] = acc.kinds[kind] || {
            assets: [],
            label: kind,
            link: linkToAssetTableWithKindFilter(kind),
          };
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          acc.kinds[kind]!.assets.push(asset);
        });
      }
      return acc;
    },
    {
      owners: {} as GroupedAssets,
      groupName: {} as GroupedAssets,
      repository: {} as GroupedAssets,
      tags: {} as GroupedAssets,
      kinds: {} as GroupedAssets,
    },
  );
}

export function useAssetHealthStatuses({
  assets,
  threadId,
  loading: assetsLoading,
}: {
  assets: AssetTableFragment[];
  threadId?: string;
  loading?: boolean;
}) {
  const assetCount = assets.length;

  const {liveDataByNode} = useAssetsHealthData({
    assetKeys: useMemo(() => assets.map((asset) => asset.key), [assets]),
    thread: threadId,
  });

  const loading = assetsLoading || assets.length > Object.keys(liveDataByNode).length;

  const {jsx, statusCounts} = useMemo(
    () => getHealthStatuses({liveDataByNode, loading, assetCount}),
    [liveDataByNode, loading, assetCount],
  );

  return {
    loading,
    statusCounts,
    jsx,
  };
}

export function getHealthStatuses({
  liveDataByNode,
  loading,
  assetCount,
}: {
  liveDataByNode: Record<string, AssetHealthFragment>;
  loading: boolean;
  assetCount: number;
}) {
  const statusCounts = Object.values(liveDataByNode).reduce(
    (acc, data) => {
      let status: AssetHealthStatus = AssetHealthStatus.UNKNOWN;
      if (data.assetHealth?.assetHealth) {
        status = data.assetHealth.assetHealth;
      }
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {} as Record<AssetHealthStatus, number>,
  );

  const degradedMeta = statusToIconAndColor[AssetHealthStatus.DEGRADED];
  const warningMeta = statusToIconAndColor[AssetHealthStatus.WARNING];
  const unknownMeta = statusToIconAndColor[AssetHealthStatus.UNKNOWN];
  const healthyMeta = statusToIconAndColor[AssetHealthStatus.HEALTHY];

  const degradedCount = statusCounts[AssetHealthStatus.DEGRADED];
  const degradedJsx = degradedCount && (
    <Popover
      content={
        <div>
          <BodySmall color={degradedMeta.textColor}>
            {compactNumberFormatter.format(degradedCount)}{' '}
            {ifPlural(degradedCount, 'asset', 'assets')} degraded
          </BodySmall>
        </div>
      }
    >
      <Box className={styles.statusCountItem}>
        <Icon name={degradedMeta.iconName} color={degradedMeta.iconColor} />
        <BodySmall color={Colors.textLight()}>
          {compactNumberFormatter.format(statusCounts[AssetHealthStatus.DEGRADED])}
        </BodySmall>
      </Box>
    </Popover>
  );

  const warningJsx = statusCounts[AssetHealthStatus.WARNING] && (
    <Box className={styles.statusCountItem}>
      <Icon name={warningMeta.iconName} color={warningMeta.iconColor} />
      <BodySmall color={Colors.textLight()}>
        {compactNumberFormatter.format(statusCounts[AssetHealthStatus.WARNING])}
      </BodySmall>
    </Box>
  );

  const unknownJsx = statusCounts[AssetHealthStatus.UNKNOWN] && (
    <Box className={styles.statusCountItem}>
      <Icon name={unknownMeta.iconName} color={unknownMeta.iconColor} />
      <BodySmall color={Colors.textLight()}>
        {compactNumberFormatter.format(statusCounts[AssetHealthStatus.UNKNOWN])}
      </BodySmall>
    </Box>
  );

  const healthyJsx = statusCounts[AssetHealthStatus.HEALTHY] && (
    <Box className={styles.statusCountItem}>
      <Icon name={healthyMeta.iconName} color={healthyMeta.iconColor} />
      <BodySmall color={Colors.textLight()}>
        {compactNumberFormatter.format(statusCounts[AssetHealthStatus.HEALTHY])}
      </BodySmall>
    </Box>
  );

  return {
    statusCounts,
    jsx: (
      <div className={styles.footer}>
        {loading ? (
          <Spinner purpose="caption-text" />
        ) : assetCount === 0 ? (
          <BodySmall color={Colors.textLight()}>No assets</BodySmall>
        ) : (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 6, wrap: 'wrap'}}>
            {healthyJsx}
            {degradedJsx}
            {warningJsx}
            {unknownJsx}
          </Box>
        )}
      </div>
    ),
  };
}

const maxThreads = 10;
let threadIdCounter = 0;
export function getThreadId() {
  threadIdCounter = (threadIdCounter + 1) % maxThreads;
  return `health-thread-${threadIdCounter}`;
}

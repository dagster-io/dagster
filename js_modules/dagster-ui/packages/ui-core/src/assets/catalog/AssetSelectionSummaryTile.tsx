import {BodySmall, Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui-components';
import clsx from 'clsx';
import React, {useEffect, useMemo} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetSelectionSummaryTile.module.css';
import {JOB_TILE_QUERY} from './JobTileQuery';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';
import {getThreadId, useAssetHealthStatuses} from './util';
import {useQuery} from '../../apollo-client';
import {JobTileQuery, JobTileQueryVariables} from './types/JobTileQuery.types';
import {RunStatusIndicator} from '../../runs/RunStatusDots';
import {TimeFromNow} from '../../ui/TimeFromNow';

export const TILE_WIDTH = 272;
export const TILE_HEIGHT = 104;
export const TILE_GAP = 12;

// An in memory cache to side step slow asset selection filtering when revisiting the page.
// To fix this properly we need to add more caches within useAssetSelectionFiltering and useAssetGraphData but it is difficult to do so
// since the array of nodes they receive aren't the same when you visit the page again since they're the result of `.filter` calls.
const memoryCache = new Map<string, {assets: any[]}>();

type Selection = {
  selection: {
    querySelection: string | null;
  };
  name: string;
  link: string;
};

export const AssetSelectionSummaryTileFromSelection = React.memo(
  ({icon, selection}: {icon: React.ReactNode; selection: Selection}) => {
    const assetSelection = selection.selection.querySelection ?? '';
    const {assets: allAssets, loading: allAssetsLoading} = useAllAssets();

    const {filtered, loading: filteredLoading} = useAssetSelectionFiltering({
      assets: allAssets,
      assetSelection,
      loading: allAssetsLoading,
      useWorker: false,
      includeExternalAssets: true,
    });

    useEffect(() => {
      if (filtered.length > 0) {
        memoryCache.set(assetSelection, {assets: filtered});
      }
    }, [filtered, assetSelection]);

    const assets = filtered.length ? filtered : (memoryCache.get(assetSelection)?.assets ?? []);

    const loading = filteredLoading && assets.length === 0;

    return (
      <AssetSelectionSummaryTile
        icon={icon}
        label={selection.name}
        assets={assets}
        link={selection.link}
        loading={loading}
      />
    );
  },
);

export const AssetSelectionSummaryTile = React.memo(
  ({
    icon,
    label,
    assets,
    link,
    loading: _assetsLoading,
  }: {
    icon: React.ReactNode;
    label: string;
    assets: AssetTableFragment[];
    link: string;
    loading?: boolean;
    threadId?: string;
  }) => {
    const {jsx, loading} = useAssetHealthStatuses({
      assets,
      threadId: useMemo(() => getThreadId(), []),
      loading: _assetsLoading,
    });

    return (
      <Link to={link} className={styles.tileLink}>
        <Box
          border="all"
          style={{
            minWidth: TILE_WIDTH,
            minHeight: TILE_HEIGHT,
          }}
          className={clsx(styles.tile, loading && styles.tileLoading)}
        >
          <div className={styles.header}>
            <div>{icon}</div>
            <div className={styles.title} style={{color: Colors.textLight()}}>
              <MiddleTruncate text={label} />
            </div>
          </div>
          <div className={styles.footer}>{jsx}</div>
        </Box>
      </Link>
    );
  },
);

const THIRTY_SECONDS = 30000;

// todo dish: Move this out of asset-related code, make tile component generic.
export const JobTile = ({name, repoAddress}: {name: string; repoAddress: RepoAddress}) => {
  const {data} = useQuery<JobTileQuery, JobTileQueryVariables>(JOB_TILE_QUERY, {
    variables: {
      pipelineSelector: {
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
        pipelineName: name,
      },
    },
    pollInterval: THIRTY_SECONDS,
  });

  const latestRun = useMemo(() => {
    const job = data?.pipelineOrError;
    if (!job || job.__typename !== 'Pipeline') {
      return null;
    }
    const {runs} = job;
    return runs[0] ?? null;
  }, [data]);

  const link = workspacePathFromAddress(repoAddress, `/jobs/${name}`);
  return (
    <Link to={link} className={styles.tileLink}>
      <Box
        border="all"
        style={{
          minWidth: TILE_WIDTH,
          minHeight: TILE_HEIGHT,
        }}
        className={styles.tile}
      >
        <div className={styles.header}>
          <div>
            <Icon name="job" size={20} />
          </div>
          <div className={styles.title} style={{color: Colors.textLight()}}>
            <MiddleTruncate text={name} />
          </div>
        </div>
        {latestRun?.startTime ? (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <RunStatusIndicator status={latestRun.runStatus} />
            <BodySmall color={Colors.textLight()}>
              launched <TimeFromNow unixTimestamp={latestRun.startTime} />
            </BodySmall>
          </Box>
        ) : null}
      </Box>
    </Link>
  );
};

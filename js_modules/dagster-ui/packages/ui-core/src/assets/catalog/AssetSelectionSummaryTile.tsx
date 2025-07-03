import {BodySmall, Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui-components';
import clsx from 'clsx';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetSelectionSummaryTile.module.css';
import {JOB_TILE_QUERY} from './JobTileQuery';
import {getHealthStatuses, getThreadId, useAssetHealthStatuses} from './util';
import {useQuery} from '../../apollo-client';
import {JobTileQuery, JobTileQueryVariables} from './types/JobTileQuery.types';
import {useSelectionHealthData} from './useSelectionHealthData';
import {RunStatusIndicator} from '../../runs/RunStatusDots';
import {TimeFromNow} from '../../ui/TimeFromNow';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export const TILE_WIDTH = 272;
export const TILE_HEIGHT = 104;
export const TILE_GAP = 12;

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

    const {liveDataByNode, loading, assetCount} = useSelectionHealthData({
      selection: assetSelection,
    });
    const {jsx} = useMemo(
      () => getHealthStatuses({liveDataByNode, loading, assetCount}),
      [liveDataByNode, loading, assetCount],
    );

    return (
      <AssetSelectionSummaryTileWithHealthStatus
        icon={icon}
        label={selection.name}
        statusJsx={jsx}
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
      <AssetSelectionSummaryTileWithHealthStatus
        icon={icon}
        label={label}
        statusJsx={jsx}
        link={link}
        loading={loading}
      />
    );
  },
);

const AssetSelectionSummaryTileWithHealthStatus = React.memo(
  ({
    icon,
    label,
    statusJsx,
    link,
    loading,
  }: {
    icon: React.ReactNode;
    label: string;
    statusJsx: React.ReactNode;
    link: string;
    loading?: boolean;
  }) => {
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
          <div className={styles.footer}>{statusJsx}</div>
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

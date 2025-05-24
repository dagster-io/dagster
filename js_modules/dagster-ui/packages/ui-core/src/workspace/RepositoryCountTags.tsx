import {Box, Tag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styles from './RepositoryCountTags.module.css';

import {DagsterRepoOption} from './WorkspaceContext/util';
import {RepoAddress} from './types';
import {workspacePathFromAddress} from './workspacePath';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

export const RepositoryCountTags = ({
  repo,
  repoAddress,
}: {
  repo: DagsterRepoOption['repository'];
  repoAddress: RepoAddress;
}) => {
  const assetGroupCount = repo.assetGroups.length;
  const jobCount = repo.pipelines.filter(({name}) => !isHiddenAssetGroupJob(name)).length;
  const scheduleCount = repo.schedules.length;
  const sensorCount = repo.sensors.length;

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Tooltip
        content={assetGroupCount === 1 ? '1 asset group' : `${assetGroupCount} asset groups`}
        placement="top"
      >
        <Link className={styles.countLink} to={workspacePathFromAddress(repoAddress, '/assets')}>
          <Tag interactive icon="asset_group">
            {assetGroupCount}
          </Tag>
        </Link>
      </Tooltip>
      <Tooltip content={jobCount === 1 ? '1 job' : `${jobCount} jobs`} placement="top">
        <Link className={styles.countLink} to={workspacePathFromAddress(repoAddress, '/jobs')}>
          <Tag interactive icon="job">
            {jobCount}
          </Tag>
        </Link>
      </Tooltip>
      <Tooltip
        content={scheduleCount === 1 ? '1 schedule' : `${scheduleCount} schedules`}
        placement="top"
      >
        <Link className={styles.countLink} to={workspacePathFromAddress(repoAddress, '/schedules')}>
          <Tag interactive icon="schedule">
            {scheduleCount}
          </Tag>
        </Link>
      </Tooltip>
      <Tooltip content={sensorCount === 1 ? '1 sensor' : `${sensorCount} sensors`} placement="top">
        <Link className={styles.countLink} to={workspacePathFromAddress(repoAddress, '/sensors')}>
          <Tag interactive icon="sensors">
            {sensorCount}
          </Tag>
        </Link>
      </Tooltip>
    </Box>
  );
};


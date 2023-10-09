import {Box, Tag} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {DagsterTag} from './RunTag';
import {RunTagsFragment} from './types/RunTable.types';

type Props = {
  repoAddress?: RepoAddress | null;
  tags: RunTagsFragment[];
};

export const CreatedByTagCell = React.memo(({repoAddress, tags}: Props) => {
  return (
    <Box flex={{direction: 'column', alignItems: 'flex-start'}}>
      <CreatedByTag repoAddress={repoAddress} tags={tags} />
    </Box>
  );
});

export const CreatedByTag = ({repoAddress, tags}: Props) => {
  const {UserDisplay} = useLaunchPadHooks();

  console.log(tags);
  const user = tags.find((tag) => tag.key === DagsterTag.User);
  if (user) {
    return <UserDisplay email={user.value} />;
  }

  const scheduleTag = tags.find((tag) => tag.key === DagsterTag.ScheduleName);
  if (scheduleTag) {
    const scheduleName = scheduleTag.value;
    const tagContent = repoAddress ? (
      <Link to={workspacePathFromAddress(repoAddress, `/schedules/${scheduleName}`)}>
        {scheduleName}
      </Link>
    ) : (
      scheduleName
    );
    return <Tag icon="schedule">{tagContent}</Tag>;
  }

  const sensorTag = tags.find((tag) => tag.key === DagsterTag.SensorName);
  if (sensorTag) {
    const sensorName = sensorTag.value;
    const tagContent = repoAddress ? (
      <Link to={workspacePathFromAddress(repoAddress, `/sensors/${sensorName}`)}>{sensorName}</Link>
    ) : (
      sensorName
    );
    return <Tag icon="sensors">{tagContent}</Tag>;
  }

  const automaterialize = tags.some(
    (tag) =>
      tag.key === DagsterTag.Automaterialize ||
      // Backwards compatibility
      (tag.key === DagsterTag.CreatedBy && tag.value === 'auto_materialize'),
  );

  if (automaterialize) {
    return <Tag icon="auto_materialize_policy">Auto-materialize policy</Tag>;
  }

  const autoObserve = tags.some((tag) => tag.key === DagsterTag.AutoObserve);
  if (autoObserve) {
    return <Tag icon="auto_observe">Auto-observation</Tag>;
  }

  return <Tag icon="account_circle">Manually launched</Tag>;
};

import {Box, Tag} from '@dagster-io/ui';
import React from 'react';

import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';

import {DagsterTag} from './RunTag';
import {RunTagsFragment} from './types/RunTable.types';

type Props = {
  tags: RunTagsFragment[];
};

export const RunCreatedByCell = React.memo(({tags}: Props) => {
  return (
    <Box flex={{direction: 'column', alignItems: 'flex-start'}}>
      <RunCreatedByTag tags={tags} />
    </Box>
  );
});

export const RunCreatedByTag = ({tags}: Props) => {
  const {UserDisplay} = useLaunchPadHooks();

  const user = tags.find((tag) => tag.key === DagsterTag.User);
  if (user) {
    return <UserDisplay email={user.value} />;
  }

  const scheduleTag = tags.find((tag) => tag.key === DagsterTag.ScheduleName);
  if (scheduleTag) {
    return <Tag icon="schedule">{scheduleTag.value}</Tag>;
  }

  const sensorTag = tags.find((tag) => tag.key === DagsterTag.SensorName);
  if (sensorTag) {
    return <Tag icon="sensors">{sensorTag.value}</Tag>;
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

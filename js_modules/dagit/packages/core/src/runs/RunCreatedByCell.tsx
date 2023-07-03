import {Box, Tag} from '@dagster-io/ui';
import React from 'react';

import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';

import {DagsterTag} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTable.types';

type Props = {
  run: RunTableRunFragment;
  onAddTag?: (tag: RunFilterToken) => void;
};

export function RunCreatedByCell(props: Props) {
  const tags = props.run.tags || [];

  const scheduleTag = tags.find((tag) => tag.key === DagsterTag.ScheduleName);
  const sensorTag = tags.find((tag) => tag.key === DagsterTag.SensorName);
  const user = tags.find((tag) => tag.key === DagsterTag.User);

  const automaterialize = tags.find(
    (tag) =>
      tag.key === DagsterTag.Automaterialize ||
      // Backwards compatibility
      (tag.key === DagsterTag.CreatedBy && tag.value === 'auto_materialize'),
  );
  const createdBy = tags.find((tag) => tag.key === DagsterTag.CreatedBy);

  const {UserDisplay} = useLaunchPadHooks();

  let creator;

  if (user) {
    creator = <UserDisplay email={user.value} />;
  } else if (scheduleTag) {
    creator = (
      <Tag icon="schedule" key="schedule">
        {scheduleTag.value}
      </Tag>
    );
  } else if (sensorTag) {
    creator = (
      <Tag icon="sensors" key="sensor">
        {sensorTag.value}
      </Tag>
    );
  } else if (automaterialize) {
    creator = (
      <Tag icon="auto_materialize_policy" key="automaterialize">
        Auto-materialize policy
      </Tag>
    );
  } else {
    creator = <Tag icon="account_circle">Manually launched</Tag>;
  }

  return (
    <Box flex={{direction: 'column', alignItems: 'flex-start'}}>{creator || createdBy?.value}</Box>
  );
}

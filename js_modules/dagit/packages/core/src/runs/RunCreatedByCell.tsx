import {Box, Tag} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';

import {DagsterTag} from './RunTag';
import {runsPathWithFilters} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTable.types';

type Props = {
  run: RunTableRunFragment;
};

export function RunCreatedByCell(props: Props) {
  const tags = props.run.tags || [];

  const isReexecution = tags.some((tag) => tag.key === DagsterTag.ParentRunId);

  const backfillTag = tags.find((tag) => tag.key === DagsterTag.Backfill);
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

  if (isReexecution || user) {
    /**
     * If this is a re-executed run then it was created by a user manually.
     * It will still have the original sensor/backfill/schedule tags because
     * they're copied over from the original but we don't show them because
     * they're only responsible for the original run
     */
    if (user) {
      creator = <UserDisplay email={user.value} />;
    } else {
      creator = <Tag icon="account_circle">Launchpad</Tag>;
    }
  } else if (backfillTag) {
    const link = props.run.assetSelection?.length
      ? `/overview/backfills/${backfillTag.value}`
      : runsPathWithFilters([
          {
            token: 'tag',
            value: `dagster/backfill=${backfillTag.value}`,
          },
        ]);
    creator = (
      <div key="backfill">
        Backfill: <Link to={link}>{backfillTag.value}</Link>
      </div>
    );
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
  }

  return (
    <Box flex={{direction: 'column', alignItems: 'flex-start'}}>{creator || createdBy?.value}</Box>
  );
}

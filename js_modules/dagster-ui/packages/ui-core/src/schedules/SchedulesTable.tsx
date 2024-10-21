import {Box, Popover, Tag} from '@dagster-io/ui-components';

import {InstigationStatus} from '../graphql/types';

export const errorDisplay = (status: InstigationStatus, runningScheduleCount: number) => {
  if (status === InstigationStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === InstigationStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === InstigationStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      'Schedule is set to be running, but either the scheduler is not configured or the scheduler is not running the schedule',
    );
  } else if (status === InstigationStatus.STOPPED && runningScheduleCount > 0) {
    errors.push('Schedule is set to be stopped, but the scheduler is still running the schedule');
  }

  if (runningScheduleCount > 0) {
    errors.push('Duplicate cron job for schedule found.');
  }

  return (
    <Popover
      interactionKind="hover"
      popoverClassName="bp5-popover-content-sizing"
      position="right"
      content={
        <Box flex={{direction: 'column', gap: 8}} padding={12}>
          <strong>There are errors with this schedule.</strong>
          <div>Errors:</div>
          <ul>
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Box>
      }
    >
      <Tag fill interactive intent="danger">
        Error
      </Tag>
    </Popover>
  );
};

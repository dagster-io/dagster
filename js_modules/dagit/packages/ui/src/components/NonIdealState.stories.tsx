import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Group} from './Group';
import {NonIdealState} from './NonIdealState';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'NonIdealState',
  component: NonIdealState,
} as Meta;

export const Default = () => {
  return (
    <Group spacing={24} direction="column">
      <NonIdealState icon="star" title="This run is currently queued." />
      <NonIdealState
        icon="star"
        title="This run is currently queued."
        action={<a href="/instance/runs?q[]=status%3AQUEUED">View queued runs</a>}
      />
      <NonIdealState
        icon="warning"
        title="No schedules found"
        description={
          <div>
            This instance does not have any schedules defined. Visit the{' '}
            <a
              href="https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors"
              target="_blank"
              rel="noreferrer"
            >
              scheduler documentation
            </a>{' '}
            for more information about scheduling runs in Dagster.
          </div>
        }
      />

      <NonIdealState
        icon="error"
        title="Query Error"
        description={
          "This is an example error message, in reality they're probably longer than this."
        }
      />
    </Group>
  );
};

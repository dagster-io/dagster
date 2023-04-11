import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui';
import * as React from 'react';

import {InstigationStatus} from '../graphql/types';

import {OpenWithIntent, ScheduleInfo, ScheduleStateChangeDialog} from './ScheduleStateChangeDialog';

interface Props {
  schedules: ScheduleInfo[];
  onDone: () => void;
}

export const ScheduleBulkActionMenu = (props: Props) => {
  const {schedules, onDone} = props;
  const count = schedules.length;

  const [openWithIntent, setOpenWithIntent] = React.useState<OpenWithIntent>('not-open');

  const {anyOff, anyOn} = React.useMemo(() => {
    let anyOff = false;
    let anyOn = false;

    for (const schedule of schedules) {
      const {
        scheduleState: {status},
      } = schedule;
      if (status === InstigationStatus.RUNNING) {
        anyOn = true;
      } else if (status === InstigationStatus.STOPPED) {
        anyOff = true;
      }
      if (anyOn && anyOff) {
        break;
      }
    }

    return {anyOff, anyOn};
  }, [schedules]);

  return (
    <>
      <Popover
        content={
          <Menu>
            <MenuItem
              text={`Start ${count === 1 ? '1 schedule' : `${count} schedules`}`}
              disabled={!anyOff}
              aria-disabled={!anyOff}
              icon="toggle_on"
              onClick={() => {
                setOpenWithIntent('start');
              }}
            />
            <MenuItem
              text={`Stop ${count === 1 ? '1 schedule' : `${count} schedules`}`}
              disabled={!anyOn}
              aria-disabled={!anyOn}
              icon="toggle_off"
              onClick={() => {
                setOpenWithIntent('stop');
              }}
            />
          </Menu>
        }
        placement="bottom-end"
      >
        <Button disabled={!count} intent="primary" rightIcon={<Icon name="expand_more" />}>
          Actions
        </Button>
      </Popover>
      <ScheduleStateChangeDialog
        openWithIntent={openWithIntent}
        schedules={schedules}
        onClose={() => setOpenWithIntent('not-open')}
        onComplete={() => {
          onDone();
        }}
      />
    </>
  );
};

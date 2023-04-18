import {useMutation} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {Button, Colors, DialogBody, DialogFooter, Dialog, Group, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {
  OpenWithIntent,
  useInstigationStateReducer,
} from '../instigation/useInstigationStateReducer';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {RepoAddress} from '../workspace/types';

import {START_SCHEDULE_MUTATION, STOP_SCHEDULE_MUTATION} from './ScheduleMutations';
import {
  StartThisScheduleMutation,
  StartThisScheduleMutationVariables,
  StopScheduleMutation,
  StopScheduleMutationVariables,
} from './types/ScheduleMutations.types';

export type ScheduleInfo = {
  repoAddress: RepoAddress;
  scheduleName: string;
  scheduleState: BasicInstigationStateFragment;
};

export interface Props {
  openWithIntent: OpenWithIntent;
  onClose: () => void;
  onComplete: () => void;
  schedules: ScheduleInfo[];
}

export const ScheduleStateChangeDialog = (props: Props) => {
  const {openWithIntent, onClose, onComplete, schedules} = props;
  const count = schedules.length;

  const [state, dispatch] = useInstigationStateReducer();

  // If the dialog is newly closed, reset state.
  React.useEffect(() => {
    if (openWithIntent === 'not-open') {
      dispatch({type: 'reset'});
    }
  }, [openWithIntent, dispatch]);

  const [startSchedule] = useMutation<
    StartThisScheduleMutation,
    StartThisScheduleMutationVariables
  >(START_SCHEDULE_MUTATION);

  const [stopSchedule] = useMutation<StopScheduleMutation, StopScheduleMutationVariables>(
    STOP_SCHEDULE_MUTATION,
  );

  const start = async (schedule: ScheduleInfo) => {
    const {repoAddress, scheduleName} = schedule;
    const variables = {
      scheduleSelector: {
        repositoryLocationName: repoAddress.location,
        repositoryName: repoAddress.name,
        scheduleName,
      },
    };

    const {data} = await startSchedule({variables});

    switch (data?.startSchedule.__typename) {
      case 'ScheduleStateResult':
        dispatch({type: 'update-success'});
        return;
      case 'UnauthorizedError':
      case 'PythonError':
        dispatch({
          type: 'update-error',
          name: scheduleName,
          error: data.startSchedule.message,
        });
    }
  };

  const stop = async (schedule: ScheduleInfo) => {
    const {scheduleName, scheduleState} = schedule;
    const variables = {
      scheduleOriginId: scheduleState.id,
      scheduleSelectorId: scheduleState.selectorId,
    };

    const {data} = await stopSchedule({variables});

    switch (data?.stopRunningSchedule.__typename) {
      case 'ScheduleStateResult':
        dispatch({type: 'update-success'});
        return;
      case 'UnauthorizedError':
      case 'PythonError':
        dispatch({
          type: 'update-error',
          name: scheduleName,
          error: data.stopRunningSchedule.message,
        });
    }
  };

  const mutate = async () => {
    if (openWithIntent === 'not-open') {
      return;
    }

    dispatch({type: 'start'});
    for (let ii = 0; ii < schedules.length; ii++) {
      const schedule = schedules[ii];
      if (openWithIntent === 'start') {
        await start(schedule);
      } else {
        await stop(schedule);
      }
    }

    dispatch({type: 'complete'});
    onComplete();
  };

  const progressContent = () => {
    if (openWithIntent === 'not-open') {
      return null;
    }

    switch (state.step) {
      case 'initial':
        if (openWithIntent === 'stop') {
          return (
            <div>
              {`${count} ${
                count === 1 ? 'schedule' : 'schedules'
              } will be stopped. Do you want to continue?`}
            </div>
          );
        }
        return (
          <div>
            {`${count} ${
              count === 1 ? 'schedule' : 'schedules'
            } will be started. Do you want to continue?`}
          </div>
        );
      case 'updating':
      case 'completed':
        const value = count > 0 ? state.completion.completed / count : 1;
        return (
          <Group direction="column" spacing={8}>
            <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
            {state.step === 'updating' ? (
              <NavigationBlock message="Schedules are being updated, please do not navigate away yet." />
            ) : null}
          </Group>
        );
      default:
        return null;
    }
  };

  const buttons = () => {
    if (openWithIntent === 'not-open') {
      return null;
    }

    switch (state.step) {
      case 'initial': {
        const label =
          openWithIntent === 'start'
            ? `Start ${count === 1 ? '1 schedule' : `${count} schedules`}`
            : `Stop ${count === 1 ? '1 schedule' : `${count} schedules`}`;
        return (
          <>
            <Button intent="none" onClick={onClose}>
              Cancel
            </Button>
            <Button intent="primary" onClick={mutate}>
              {label}
            </Button>
          </>
        );
      }
      case 'updating': {
        const label =
          openWithIntent === 'start'
            ? `Starting ${count === 1 ? '1 schedule' : `${count} schedules`}`
            : `Stopping ${count === 1 ? '1 schedule' : `${count} schedules`}`;
        return (
          <Button intent="primary" disabled>
            {label}
          </Button>
        );
      }
      case 'completed':
        return (
          <Button intent="primary" onClick={onClose}>
            Done
          </Button>
        );
    }
  };

  const completionContent = () => {
    if (openWithIntent === 'not-open' || state.step === 'initial') {
      return null;
    }

    if (state.step === 'updating') {
      return (
        <div>
          Please do not close the window or navigate away while schedules are being updated.
        </div>
      );
    }

    const errors = state.completion.errors;
    const errorCount = Object.keys(errors).length;
    const successCount = state.completion.completed - errorCount;

    return (
      <Group direction="column" spacing={8}>
        {successCount ? (
          <Group direction="row" spacing={8} alignItems="flex-start">
            <Icon name="check_circle" color={Colors.Green500} />
            <div>
              {openWithIntent === 'start'
                ? `Successfully started ${
                    successCount === 1 ? '1 schedule' : `${successCount} schedules`
                  }.`
                : `Successfully stopped ${
                    successCount === 1 ? '1 schedule' : `${successCount} schedules`
                  }.`}
            </div>
          </Group>
        ) : null}
        {errorCount ? (
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8} alignItems="flex-start">
              <Icon name="warning" color={Colors.Yellow500} />
              <div>
                {openWithIntent === 'start'
                  ? `Could not start ${
                      errorCount === 1 ? '1 schedule' : `${errorCount} schedules`
                    }.`
                  : `Could not stop ${
                      errorCount === 1 ? '1 schedule' : `${errorCount} schedules`
                    }.`}
              </div>
            </Group>
            <ul>
              {Object.keys(errors).map((scheduleName) => (
                <li key={scheduleName}>
                  <Group direction="row" spacing={8}>
                    <strong>{scheduleName}:</strong>
                    {errors[scheduleName] ? <div>{errors[scheduleName]}</div> : null}
                  </Group>
                </li>
              ))}
            </ul>
          </Group>
        ) : null}
      </Group>
    );
  };

  const canQuicklyClose = state.step !== 'updating';

  return (
    <Dialog
      isOpen={openWithIntent !== 'not-open'}
      title={openWithIntent === 'start' ? 'Start schedules' : 'Stop schedules'}
      canEscapeKeyClose={canQuicklyClose}
      canOutsideClickClose={canQuicklyClose}
      onClose={onClose}
    >
      <DialogBody>
        <Group direction="column" spacing={24}>
          {progressContent()}
          {completionContent()}
        </Group>
      </DialogBody>
      <DialogFooter>{buttons()}</DialogFooter>
    </Dialog>
  );
};

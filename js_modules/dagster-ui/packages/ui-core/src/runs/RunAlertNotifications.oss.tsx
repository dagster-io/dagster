import {Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useCallback, useEffect, useState} from 'react';

import {
  NOTIFY_RUN_IDS_CHANGED,
  isObservingRunCompletion,
  observeRunCompletion,
  unobserveRunCompletion,
} from './RunCompletionNotificationObserver';
import {RunStatus} from '../graphql/types';

const doneStatuses = new Set<RunStatus>([RunStatus.SUCCESS, RunStatus.FAILURE, RunStatus.CANCELED]);

export const RunAlertNotifications = ({
  runId,
  runStatus,
}: {
  runId: string;
  runStatus: RunStatus;
}) => {
  const [notifyOn, setNotifyOn] = useState(() => isObservingRunCompletion(runId));

  useEffect(() => {
    const handler = () => setNotifyOn(isObservingRunCompletion(runId));
    document.addEventListener(NOTIFY_RUN_IDS_CHANGED, handler);
    return () => document.removeEventListener(NOTIFY_RUN_IDS_CHANGED, handler);
  }, [runId]);

  const isDone = doneStatuses.has(runStatus);

  const handleToggle = useCallback(() => {
    if (isDone) return;
    if (notifyOn) {
      unobserveRunCompletion(runId);
      setNotifyOn(false);
    } else {
      if (typeof Notification !== 'undefined' && Notification.permission === 'default')
        Notification.requestPermission();
      observeRunCompletion(runId);
      setNotifyOn(true);
    }
  }, [runId, notifyOn, isDone]);

  return (
    <Tooltip
      content={
        isDone
          ? 'Notifications are not available for completed runs'
          : notifyOn
            ? 'In-app notification when this run completes (on)'
            : 'Notify when this run completes'
      }
    >
      <Button icon={<Icon name="notifications" />} disabled={isDone} onClick={handleToggle}>
        {notifyOn ? 'Notifications on' : 'Notify on completion'}
      </Button>
    </Tooltip>
  );
};

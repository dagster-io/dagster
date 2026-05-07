import {Colors, Icon, Popover, Spinner} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {memo} from 'react';

import {RunStats} from './RunStats';
import {RUN_STATUS_COLORS} from './RunStatusTag';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';
import styles from './css/RunStatusDots.module.css';
import {RunStatus} from '../graphql/types';

export const RunStatusWithStats = memo(
  ({
    runId,
    ...rest
  }: RunStatusProps & {
    runId: string;
  }) => (
    <Popover
      position="bottom"
      interactionKind="hover"
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
    >
      <RunStatusIndicator {...rest} />
    </Popover>
  ),
);

interface RunStatusProps {
  status: RunStatus | 'SCHEDULED';
  size?: number;
}

export const RunStatusIndicator = memo(({status, size}: RunStatusProps) => {
  if (status === 'STARTED' || status === 'CANCELING') {
    return <Spinner purpose="caption-text" />;
  }
  if (status === 'SCHEDULED') {
    return <RunStatusDot status={status} size={size || 12} />;
  }
  if (status === 'SUCCESS') {
    return <Icon name="run_success" color={Colors.accentGreen()} size={16} />;
  }
  if (status === 'FAILURE') {
    return <Icon name="run_failed" color={Colors.accentRed()} size={16} />;
  }
  if (status === 'CANCELED') {
    return <Icon name="run_canceled" color={Colors.accentGray()} size={16} />;
  }
  return (
    <RunStatusDot
      status={status}
      size={size || 12}
      pulse={inProgressStatuses.has(status) || queuedStatuses.has(status)}
    />
  );
});

export const RunStatusDot = ({
  status,
  size,
  pulse,
}: {
  status: RunStatus | 'SCHEDULED';
  size: number;
  pulse?: boolean;
}) => (
  <div
    className={clsx(styles.runStatusDot, pulse && styles.pulse)}
    style={{
      width: size,
      height: size,
      borderRadius: size / 2,
      background: RUN_STATUS_COLORS[status],
    }}
  />
);

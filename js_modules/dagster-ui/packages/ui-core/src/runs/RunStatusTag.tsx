import {Box, CaptionMono, Colors, Popover, Tag} from '@dagster-io/ui-components';

import {RunStats} from './RunStats';
import {RunStatusIndicator} from './RunStatusDots';
import {assertUnreachable} from '../app/Util';
import {RunStatus} from '../graphql/types';

const statusToIntent = (status: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
    case RunStatus.NOT_STARTED:
    case RunStatus.CANCELED:
    case RunStatus.MANAGED:
      return 'none';
    case RunStatus.SUCCESS:
      return 'success';
    case RunStatus.FAILURE:
      return 'danger';
    case RunStatus.STARTING:
    case RunStatus.STARTED:
    case RunStatus.CANCELING:
      return 'primary';
    default:
      return assertUnreachable(status);
  }
};

const runStatusToString = (status: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
      return '排队中';
    case RunStatus.SUCCESS:
      return '成功';
    case RunStatus.STARTING:
      return '启动中';
    case RunStatus.NOT_STARTED:
      return '未开始';
    case RunStatus.FAILURE:
      return '失败';
    case RunStatus.STARTED:
      return '执行中';
    case RunStatus.MANAGED:
      return '托管中';
    case RunStatus.CANCELING:
      return '取消中';
    case RunStatus.CANCELED:
      return '已取消';
    default:
      return assertUnreachable(status);
  }
};

export const runStatusToBackfillStateString = (status: RunStatus) => {
  switch (status) {
    case RunStatus.CANCELED:
      return '已取消';
    case RunStatus.CANCELING:
      return '取消中';
    case RunStatus.FAILURE:
      return '失败';
    case RunStatus.STARTING:
    case RunStatus.STARTED:
      return '进行中';
    case RunStatus.QUEUED:
      return '排队中';
    case RunStatus.SUCCESS:
      return '已完成';
    case RunStatus.MANAGED:
    case RunStatus.NOT_STARTED:
      return '缺失';
    default:
      return assertUnreachable(status);
  }
};

export const RUN_STATUS_COLORS = {
  QUEUED: Colors.accentGray(),
  NOT_STARTED: Colors.accentGrayHover(),
  MANAGED: Colors.accentGray(),
  STARTED: Colors.accentBlue(),
  STARTING: Colors.accentBlue(),
  CANCELING: Colors.accentBlue(),
  SUCCESS: Colors.accentGreen(),
  FAILURE: Colors.accentRed(),
  CANCELED: Colors.accentRed(),

  // Not technically a RunStatus, but useful.
  SCHEDULED: Colors.accentGray(),
};

export const RunStatusTag = (props: {status: RunStatus}) => {
  const {status} = props;
  return (
    <Tag intent={statusToIntent(status)}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={status} size={10} />
        <div>{runStatusToString(status)}</div>
      </Box>
    </Tag>
  );
};

export const RunStatusTagWithID = ({runId, status}: {runId: string; status: RunStatus}) => {
  return (
    <Tag intent={statusToIntent(status)}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={status} size={10} />
        <CaptionMono>{runId.slice(0, 8)}</CaptionMono>
      </Box>
    </Tag>
  );
};

interface Props {
  runId: string;
  status: RunStatus;
}

export const RunStatusTagWithStats = (props: Props) => {
  const {runId, status} = props;
  return (
    <Popover
      position="bottom-left"
      interactionKind="hover"
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
      usePortal
    >
      <RunStatusTag status={status} />
    </Popover>
  );
};

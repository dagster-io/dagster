import {Body2, Box, CaptionMono, Colors, Icon, Popover, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {RunStats} from './RunStats';
import {RunStatusIndicator} from './RunStatusDots';
import {assertUnreachable} from '../app/Util';
import {AssetCheckSeverity, RunStatus} from '../graphql/types';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTableEntryFragment.types';

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
      return 'Queued';
    case RunStatus.SUCCESS:
      return 'Success';
    case RunStatus.STARTING:
      return 'Starting';
    case RunStatus.NOT_STARTED:
      return 'Not started';
    case RunStatus.FAILURE:
      return 'Failure';
    case RunStatus.STARTED:
      return 'Started';
    case RunStatus.MANAGED:
      return 'Managed';
    case RunStatus.CANCELING:
      return 'Canceling';
    case RunStatus.CANCELED:
      return 'Canceled';
    default:
      return assertUnreachable(status);
  }
};

export const runStatusToBackfillStateString = (status: RunStatus) => {
  switch (status) {
    case RunStatus.CANCELED:
      return 'Canceled';
    case RunStatus.CANCELING:
      return 'Canceling';
    case RunStatus.FAILURE:
      return 'Failed';
    case RunStatus.STARTING:
    case RunStatus.STARTED:
      return 'In progress';
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.SUCCESS:
      return 'Completed';
    case RunStatus.MANAGED:
    case RunStatus.NOT_STARTED:
      return 'Missing';
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

type RunsFeedEntryRun = Extract<RunsFeedTableEntryFragment, {__typename: 'Run'}>;
type RunAssetCheckEvaluation = RunsFeedEntryRun['assetCheckEvaluations'][number];

const getRunChecksSummary = (evaluations?: RunAssetCheckEvaluation[] | null) => {
  if (!evaluations || evaluations.length === 0) {
    return null;
  }

  const totalCount = evaluations.length;
  const failedCount = evaluations.filter((e) => !e.success).length;

  if (failedCount === 0) {
    return null;
  }

  const label = `(${failedCount}/${totalCount})`;
  const summaryText =
    totalCount === 1
      ? '1 asset check failed'
      : `${failedCount} of ${totalCount} asset checks failed`;

  return {evaluations, label, summaryText};
};

type ChecksTagIntent = 'warning' | 'danger';

const checksTagIntent = (evaluations: RunAssetCheckEvaluation[]): ChecksTagIntent => {
  const failed = evaluations.filter((e) => !e.success);
  const hasErrorFailure = failed.some((e) => e.severity === AssetCheckSeverity.ERROR);
  return hasErrorFailure ? 'danger' : 'warning';
};

const iconForEvaluation = (e: RunAssetCheckEvaluation) => {
  if (e.success) {
    return <Icon name="check_circle" color={Colors.accentGreen()} />;
  }
  if (e.severity === AssetCheckSeverity.WARN) {
    return <Icon name="warning_outline" color={Colors.accentYellow()} />;
  }
  return <Icon name="cancel" color={Colors.accentRed()} />;
};

const evaluationKey = (e: RunAssetCheckEvaluation) => {
  const assetKeyStr = e.assetKey.path.join('/');
  return `${e.checkName}-${assetKeyStr}-${e.timestamp}`;
};

const severityRank = (s: AssetCheckSeverity) => {
  // Lower number = earlier in list
  switch (s) {
    case AssetCheckSeverity.ERROR:
      return 0;
    case AssetCheckSeverity.WARN:
      return 1;
    default:
      return 2;
  }
};

export const RunChecksTag = ({label, intent}: {label: string; intent: ChecksTagIntent}) => {
  return (
    <Tag intent={intent}>
      <CaptionMono>{label}</CaptionMono>
    </Tag>
  );
};

const RunChecksPopoverContent = ({
  evaluations,
  summaryText,
}: {
  evaluations: RunAssetCheckEvaluation[];
  summaryText: string;
}) => {
  const sorted = useMemo(() => {
    return [...evaluations].sort((a, b) => {
      if (a.success !== b.success) {
        return a.success ? 1 : -1;
      }

      if (!a.success && !b.success && a.severity !== b.severity) {
        return severityRank(a.severity) - severityRank(b.severity);
      }

      const aAsset = a.assetKey.path.join('/');
      const bAsset = b.assetKey.path.join('/');
      const assetCmp = aAsset.localeCompare(bAsset);
      if (assetCmp !== 0) {
        return assetCmp;
      }

      const nameCmp = a.checkName.localeCompare(b.checkName);
      if (nameCmp !== 0) {
        return nameCmp;
      }

      return b.timestamp - a.timestamp;
    });
  }, [evaluations]);

  return (
    <Box padding={12} flex={{direction: 'column', gap: 6}} style={{maxWidth: 420}}>
      <Body2>{summaryText}</Body2>

      <Box
        flex={{direction: 'column', gap: 6}}
        style={{
          maxHeight: 240,
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        {sorted.map((e) => (
          <Box
            key={evaluationKey(e)}
            flex={{direction: 'row', alignItems: 'center', gap: 8}}
            style={{minWidth: 0}}
          >
            {iconForEvaluation(e)}
            <CaptionMono
              style={{flex: 1, minWidth: 0, whiteSpace: 'normal', overflowWrap: 'anywhere'}}
            >
              {e.checkName}
            </CaptionMono>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export const RunChecksTagWithPopover = ({
  evaluations,
}: {
  evaluations?: RunAssetCheckEvaluation[] | null;
}) => {
  const summary = getRunChecksSummary(evaluations);
  if (!summary) {
    return null;
  }

  const intent = checksTagIntent(summary.evaluations);

  return (
    <Popover
      position="bottom-left"
      interactionKind="hover"
      hoverOpenDelay={150}
      usePortal
      content={
        <RunChecksPopoverContent
          evaluations={summary.evaluations}
          summaryText={summary.summaryText}
        />
      }
    >
      <RunChecksTag label={summary.label} intent={intent} />
    </Popover>
  );
};

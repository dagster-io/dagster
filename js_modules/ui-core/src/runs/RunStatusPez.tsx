import {Box, CaptionMono, Colors, Popover} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {RunStatusIndicator} from './RunStatusDots';
import {RUN_STATUS_COLORS} from './RunStatusTag';
import {failedStatuses, inProgressStatuses} from './RunStatuses';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {RunTimeFragment} from './types/RunUtils.types';
import {RunStatus} from '../graphql/types';
import {StepSummaryForRun} from '../instance/StepSummaryForRun';
import {PezItem} from '../ui/PezItem';
import styles from './css/RunStatusPez.module.css';

const MIN_OPACITY = 0.2;
const MAX_OPACITY = 1.0;
const MIN_OPACITY_STEPS = 3;

interface Props {
  opacity?: number;
  runId: string;
  status: RunStatus;
}

export const RunStatusPez = (props: Props) => {
  const {status, opacity = MAX_OPACITY} = props;
  const color = RUN_STATUS_COLORS[status];

  return <div className={styles.pez} style={{backgroundColor: color, opacity}} />;
};

interface ListProps {
  fade: boolean;
  jobName: string;
  runs: RunTimeFragment[];
  forceCount?: number;
}

export const RunStatusPezList = (props: ListProps) => {
  const {fade, jobName, runs, forceCount} = props;
  const count = runs.length;
  const countForStep = Math.max(MIN_OPACITY_STEPS, count);
  const step = (MAX_OPACITY - MIN_OPACITY) / countForStep;

  let items: (RunTimeFragment | null)[] = [...runs];
  if (forceCount) {
    if (forceCount > items.length) {
      items.unshift(...Array(forceCount - items.length).fill(null));
    } else {
      items = items.slice(0, forceCount);
    }
  }

  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
      {items.map((run, ii) => {
        const opacity = fade ? MAX_OPACITY - (count - ii - 1) * step : 1.0;
        if (!run) {
          return (
            <PezItem key={`empty-${ii}`} color={Colors.backgroundLighter()} opacity={opacity} />
          );
        }

        return (
          <Popover
            key={run.id}
            position="top"
            interactionKind="hover"
            content={
              <div>
                <RunStatusOverlay run={run} name={jobName} />
              </div>
            }
            hoverOpenDelay={100}
          >
            <PezItem key={run.id} color={RUN_STATUS_COLORS[run.status]} opacity={opacity} />
          </Popover>
        );
      })}
    </Box>
  );
};

interface OverlayProps {
  run: RunTimeFragment;
  name: string;
}

export const RunStatusOverlay = ({name, run}: OverlayProps) => {
  return (
    <div className={styles.overlayContainer}>
      <div className={styles.overlayTitle}>{name}</div>
      <div className={styles.runRow}>
        <Box flex={{alignItems: 'center', direction: 'row', gap: 8}}>
          <RunStatusIndicator status={run.status} />
          <Link to={`/runs/${run.id}`}>
            <CaptionMono>{titleForRun(run)}</CaptionMono>
          </Link>
        </Box>
        <Box flex={{direction: 'column', gap: 4}}>
          <RunTime run={run} />
          <RunStateSummary run={run} />
        </Box>
      </div>
      {failedStatuses.has(run.status) || inProgressStatuses.has(run.status) ? (
        <div className={styles.summaryContainer}>
          <StepSummaryForRun runId={run.id} />
        </div>
      ) : null}
    </div>
  );
};

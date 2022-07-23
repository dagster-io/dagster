import {Box, Tag} from '@dagster-io/ui';
import * as React from 'react';

import {RunStatusIndicator} from '../runs/RunStatusDots';
import {failedStatuses, inProgressStatuses} from '../runs/RunStatuses';
import {RunStateSummary, RunTime} from '../runs/RunUtils';
import {RunTimeFragment} from '../runs/types/RunTimeFragment';
import {RunStatus} from '../types/globalTypes';
import {AnchorButton} from '../ui/AnchorButton';

import {StepSummaryForRun} from './StepSummaryForRun';

export const LastRunSummary: React.FC<{run: RunTimeFragment}> = React.memo(({run}) => {
  const {status} = run;

  const intent = React.useMemo(() => {
    switch (status) {
      case RunStatus.SUCCESS:
        return 'success';
      case RunStatus.CANCELED:
      case RunStatus.CANCELING:
      case RunStatus.FAILURE:
        return 'danger';
      default:
        return 'none';
    }
  }, [status]);

  return (
    <Box
      flex={{
        direction: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 16,
      }}
    >
      <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Tag intent={intent}>
            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
              <RunStatusIndicator status={run.status} size={10} />
              <RunTime run={run} />
            </Box>
          </Tag>
          <RunStateSummary run={run} />
        </Box>
        {failedStatuses.has(run.status) || inProgressStatuses.has(run.status) ? (
          <StepSummaryForRun runId={run.id} />
        ) : undefined}
      </Box>
      <AnchorButton to={`/instance/runs/${run.id}`}>View run</AnchorButton>
    </Box>
  );
});

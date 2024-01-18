import {Box, Popover, Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {StepSummaryForRun} from './StepSummaryForRun';
import {RunStatus} from '../graphql/types';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RunStatusOverlay} from '../runs/RunStatusPez';
import {failedStatuses, inProgressStatuses} from '../runs/RunStatuses';
import {RunStateSummary, RunTime} from '../runs/RunUtils';
import {RunTimeFragment} from '../runs/types/RunUtils.types';
import {AnchorButton} from '../ui/AnchorButton';

interface Props {
  name: string;
  run: RunTimeFragment;
  showHover?: boolean;
  showButton?: boolean;
  showSummary?: boolean;
}

export const LastRunSummary = React.memo(
  ({name, run, showHover = false, showButton = true, showSummary = true}: Props) => {
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

    const tag = () => {
      const tagElement = (
        <Tag intent={intent}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <RunStatusIndicator status={run.status} size={10} />
            <RunTime run={run} />
          </Box>
        </Tag>
      );

      if (!showHover) {
        return tagElement;
      }

      return (
        <Popover
          position="top"
          interactionKind="hover"
          content={
            <div>
              <RunStatusOverlay run={run} name={name} />
            </div>
          }
          hoverOpenDelay={100}
        >
          {tagElement}
        </Popover>
      );
    };

    return (
      <Box
        flex={{
          direction: 'row',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 16,
        }}
      >
        <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 4}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            {tag()}
            {showSummary ? <RunStateSummary run={run} /> : null}
          </Box>
          {showSummary && (failedStatuses.has(run.status) || inProgressStatuses.has(run.status)) ? (
            <StepSummaryForRun runId={run.id} />
          ) : undefined}
        </Box>
        {showButton ? <AnchorButton to={`/runs/${run.id}`}>View run</AnchorButton> : null}
      </Box>
    );
  },
);

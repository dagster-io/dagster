import {gql} from '@apollo/client';
import {Button, Classes, Colors, Dialog} from '@blueprintjs/core';
import * as React from 'react';

import {RunTags} from 'src/runs/RunTags';
import {TimeElapsed} from 'src/runs/TimeElapsed';
import {RunDetailsFragment} from 'src/runs/types/RunDetailsFragment';
import {RunFragment} from 'src/runs/types/RunFragment';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {HighlightedCodeBlock} from 'src/ui/HighlightedCodeBlock';
import {MetadataTable} from 'src/ui/MetadataTable';

const timingStringForStatus = (status?: PipelineRunStatus) => {
  switch (status) {
    case PipelineRunStatus.QUEUED:
      return 'Queued';
    case PipelineRunStatus.CANCELED:
      return 'Canceled';
    case PipelineRunStatus.CANCELING:
      return 'Canceling…';
    case PipelineRunStatus.FAILURE:
      return 'Failed';
    case PipelineRunStatus.NOT_STARTED:
      return 'Waiting to start…';
    case PipelineRunStatus.STARTED:
      return 'Running…';
    case PipelineRunStatus.STARTING:
      return 'Starting…';
    case PipelineRunStatus.SUCCESS:
      return 'Succeeded';
    default:
      return 'None';
  }
};

const LoadingOrValue: React.FC<{
  loading: boolean;
  children: () => React.ReactNode;
}> = ({loading, children}) =>
  loading ? <div style={{color: Colors.GRAY3}}>Loading…</div> : <div>{children()}</div>;

export const RunDetails: React.FC<{
  loading: boolean;
  run: RunDetailsFragment | undefined;
}> = ({loading, run}) => {
  return (
    <MetadataTable
      spacing={0}
      rows={[
        {
          key: 'Started',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'PipelineRunStatsSnapshot' && run.stats.startTime) {
                  return (
                    <TimestampDisplay
                      timestamp={run.stats.startTime}
                      format="MMM D, YYYY, h:mm:ss A"
                    />
                  );
                }
                return (
                  <div style={{color: Colors.GRAY3}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Ended',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'PipelineRunStatsSnapshot' && run.stats.endTime) {
                  return (
                    <TimestampDisplay
                      timestamp={run.stats.endTime}
                      format="MMM D, YYYY, h:mm:ss A"
                    />
                  );
                }
                return (
                  <div style={{color: Colors.GRAY3}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Duration',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'PipelineRunStatsSnapshot' && run.stats.startTime) {
                  return (
                    <TimeElapsed startUnix={run.stats.startTime} endUnix={run.stats.endTime} />
                  );
                }
                return (
                  <div style={{color: Colors.GRAY3}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
      ]}
    />
  );
};

export const RunConfigDialog: React.FC<{run: RunFragment}> = ({run}) => {
  const [showDialog, setShowDialog] = React.useState(false);
  return (
    <div>
      <Button onClick={() => setShowDialog(true)}>View tags and configuration</Button>
      <Dialog
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        style={{width: '800px'}}
        title="Run configuration"
      >
        <div className={Classes.DIALOG_BODY}>
          <Group direction="column" spacing={20}>
            <Group direction="column" spacing={12}>
              <div style={{fontSize: '16px', fontWeight: 600}}>Tags</div>
              <div>
                <RunTags tags={run.tags} />
              </div>
            </Group>
            <Group direction="column" spacing={12}>
              <div style={{fontSize: '16px', fontWeight: 600}}>Config</div>
              <HighlightedCodeBlock value={run?.runConfigYaml || ''} language="yaml" />
            </Group>
          </Group>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={() => setShowDialog(false)} intent="primary">
              OK
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export const RUN_DETAILS_FRAGMENT = gql`
  fragment RunDetailsFragment on PipelineRun {
    id
    stats {
      ... on PipelineRunStatsSnapshot {
        id
        endTime
        startTime
      }
    }
    status
  }
`;

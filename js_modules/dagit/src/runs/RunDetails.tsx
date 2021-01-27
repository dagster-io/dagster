import {gql} from '@apollo/client';
import {Button, Classes, Colors, Dialog} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {RunTags} from 'src/runs/RunTags';
import {TimeElapsed} from 'src/runs/TimeElapsed';
import {RunFragment} from 'src/runs/types/RunFragment';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {HighlightedCodeBlock} from 'src/ui/HighlightedCodeBlock';
import {MetadataTable} from 'src/ui/MetadataTable';
import {FontFamily} from 'src/ui/styles';

const timingStringForStatus = (status?: PipelineRunStatus) => {
  switch (status) {
    case PipelineRunStatus.QUEUED:
      return 'Queued';
    case PipelineRunStatus.CANCELED:
      return 'Canceled';
    case PipelineRunStatus.CANCELING:
      return 'Canceling…';
    default:
      return 'Running…';
  }
};

const LoadingOrValue: React.FC<{
  loading: boolean;
  children: () => React.ReactNode;
}> = ({loading, children}) =>
  loading ? <div style={{color: Colors.GRAY3}}>Loading…</div> : <div>{children()}</div>;

export const RunDetails: React.FC<{
  loading: boolean;
  run: RunFragment | undefined;
}> = ({loading, run}) => {
  const [showDialog, setShowDialog] = React.useState(false);

  return (
    <Box
      padding={{vertical: 8, horizontal: 12}}
      border={{side: 'bottom', width: 1, color: Colors.GRAY5}}
      flex={{justifyContent: 'space-between'}}
    >
      <Group direction="row" spacing={12}>
        <Box padding={{right: 12}} border={{side: 'right', width: 1, color: Colors.LIGHT_GRAY3}}>
          <MetadataTable
            spacing={0}
            rows={[
              {
                key: 'Pipeline',
                value: (
                  <LoadingOrValue loading={loading}>
                    {() => (
                      <div>
                        {run?.pipeline.name}{' '}
                        <span style={{fontFamily: FontFamily.monospace}}>
                          (
                          <Link
                            to={`/instance/snapshots/${run?.pipeline.name}@${run?.pipelineSnapshotId}`}
                          >
                            {run?.pipelineSnapshotId?.slice(0, 8)}
                          </Link>
                          )
                        </span>
                      </div>
                    )}
                  </LoadingOrValue>
                ),
              },
              {
                key: 'Duration',
                value: (
                  <LoadingOrValue loading={loading}>
                    {() => {
                      if (
                        run?.stats.__typename === 'PipelineRunStatsSnapshot' &&
                        run.stats.startTime
                      ) {
                        return (
                          <TimeElapsed
                            startUnix={run.stats.startTime}
                            endUnix={run.stats.endTime}
                          />
                        );
                      }
                      return (
                        <div style={{color: Colors.GRAY3}}>
                          {timingStringForStatus(run?.status)}
                        </div>
                      );
                    }}
                  </LoadingOrValue>
                ),
              },
            ]}
          />
        </Box>
        <Box padding={{right: 12}}>
          <MetadataTable
            spacing={0}
            rows={[
              {
                key: 'Started',
                value: (
                  <LoadingOrValue loading={loading}>
                    {() => {
                      if (
                        run?.stats.__typename === 'PipelineRunStatsSnapshot' &&
                        run.stats.startTime
                      ) {
                        return (
                          <TimestampDisplay
                            timestamp={run.stats.startTime}
                            format="MMM D, YYYY, h:mm:ss A"
                          />
                        );
                      }
                      return (
                        <div style={{color: Colors.GRAY3}}>
                          {timingStringForStatus(run?.status)}
                        </div>
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
                      if (
                        run?.stats.__typename === 'PipelineRunStatsSnapshot' &&
                        run.stats.endTime
                      ) {
                        return (
                          <TimestampDisplay
                            timestamp={run.stats.endTime}
                            format="MMM D, YYYY, h:mm:ss A"
                          />
                        );
                      }
                      return (
                        <div style={{color: Colors.GRAY3}}>
                          {timingStringForStatus(run?.status)}
                        </div>
                      );
                    }}
                  </LoadingOrValue>
                ),
              },
            ]}
          />
        </Box>
      </Group>
      {run ? (
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
      ) : null}
    </Box>
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

import {gql} from '@apollo/client';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {PipelineRunStatus} from '../types/globalTypes';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {HighlightedCodeBlock} from '../ui/HighlightedCodeBlock';
import {IconWIP} from '../ui/Icon';
import {MetadataTable} from '../ui/MetadataTable';

import {RunTags} from './RunTags';
import {TimeElapsed} from './TimeElapsed';
import {RunDetailsFragment} from './types/RunDetailsFragment';
import {RunFragment} from './types/RunFragment';

export const timingStringForStatus = (status?: PipelineRunStatus) => {
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
      return 'Started…';
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
  loading ? <div style={{color: ColorsWIP.Gray400}}>Loading…</div> : <div>{children()}</div>;

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

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
                    <TimestampDisplay timestamp={run.stats.startTime} timeFormat={TIME_FORMAT} />
                  );
                }
                return (
                  <div style={{color: ColorsWIP.Gray400}}>{timingStringForStatus(run?.status)}</div>
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
                    <TimestampDisplay timestamp={run.stats.endTime} timeFormat={TIME_FORMAT} />
                  );
                }
                return (
                  <div style={{color: ColorsWIP.Gray400}}>{timingStringForStatus(run?.status)}</div>
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
                  <div style={{color: ColorsWIP.Gray400}}>{timingStringForStatus(run?.status)}</div>
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
  const {rootServerURI} = React.useContext(AppContext);
  return (
    <div>
      <Group direction="row" spacing={8}>
        <ButtonWIP icon={<IconWIP name="local_offer" />} onClick={() => setShowDialog(true)}>
          View tags and config
        </ButtonWIP>
        <Tooltip content="Loadable in dagit-debug" position="bottom-right">
          <ButtonWIP
            icon={<IconWIP name="download_for_offline" />}
            onClick={() => window.open(`${rootServerURI}/download_debug/${run.runId}`)}
          >
            Debug file
          </ButtonWIP>
        </Tooltip>
      </Group>
      <DialogWIP
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        style={{width: '800px'}}
        title="Run configuration"
      >
        <DialogBody>
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
        </DialogBody>
        <DialogFooter>
          <ButtonWIP onClick={() => setShowDialog(false)} intent="primary">
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
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
